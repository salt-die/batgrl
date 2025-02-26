import asyncio
import os
import re
from collections.abc import Callable
from typing import Literal

from ..colors import Color
from ..geometry import Size, Point
from ._fbuf cimport(
    fbuf,
    fbuf_endswith,
    fbuf_equals,
    fbuf_flush_fd,
    fbuf_free,
    fbuf_init,
    fbuf_put_char,
    fbuf_putn,
    fbuf_read_fd,
    fbuf_small_init,
)
from .ansi_escapes import ANSI_ESCAPES
from .events import (
    ColorReportEvent,
    CursorPositionReportEvent,
    DECReplyModeEvent,
    DeviceAttributesReportEvent,
    Event,
    FocusEvent,
    KeyEvent,
    MouseEvent,
    PasteEvent,
    PixelGeometryReportEvent,
    ResizeEvent,
    UnknownEscapeSequence,
)

DEF MAX_PARAMS = 32
DEF PASTE_START = b"\x1b[200~"
DEF PASTE_END = b"\x1b[201~"
DEF STRING_TERMINATOR = b"\x1b\\"
DEF FOCUS_IN = b"\x1b[I"
DEF FOCUS_OUT = b"\x1b[O"

ESCAPE_TIMEOUT: float = 0.05
DSR_REQUEST_TIMEOUT: float = 0.1
COLOR_RE: re.Pattern[bytes] = re.compile(
    rb"\x1b\]1([10]);rgb:"
    rb"([0-9a-f]{2})[0-9a-f]{2}/"
    rb"([0-9a-f]{2})[0-9a-f]{2}/"
    rb"([0-9a-f]{2})[0-9a-f]{2}\x1b\\"
)
DEC_MODES: frozenset[bytes] = frozenset([1016, 2026])


cdef int csi_params(const fbuf *f, char *initial, char* final, uint *params):
    final[0] = f.buf[f.len - 1]
    if f.len == 3:
        return 0

    cdef uint param_start = 2
    if not (0x30 <= f.buf[2] <= 0x39 or f.buf[2] == 0x3b):
        initial[0] = f.buf[2]
        if f.len == 4:
            return 0
        param_start += 1

    cdef uint param_end
    if f.buf[f.len - 2] == 0x24:
        # DECRPM
        param_end = f.len - 2
    else:
        param_end = f.len - 1

    cdef:
        size_t i
        int nparams = 0
        uint param = 0

    for i in range(param_start, param_end):
        if f.buf[i] == 0x3b:
            params[nparams] = param
            nparams += 1
            if nparams == MAX_PARAMS:
                # Too many params.
                return -1
            param = 0
        else:
            param *= 10
            param += f.buf[i] - 0x30

    params[nparams] = param
    nparams += 1
    return nparams


cdef class Vt100Terminal:
    def __cinit__(self):
        if fbuf_small_init(&self.read_buf):
            raise MemoryError
        if fbuf_small_init(&self.in_buf):
            fbuf_free(&self.read_buf)
            raise MemoryError
        if fbuf_init(&self.out_buf):
            fbuf_free(&self.read_buf)
            fbuf_free(&self.in_buf)
            raise MemoryError
        self.state = GROUND
        self.last_y = 0
        self.last_x = 0
        self.skip_newline = 0
        self.sum_supported = 0
        self.sgr_pixels_supported = 0
        self.pixel_geometry_reported = 0
        self.pixel_mouse_mode = 0

    def __dealloc__(self):
        fbuf_free(&self.read_buf)
        fbuf_free(&self.in_buf)
        fbuf_free(&self.out_buf)

    def __init__(self, stdin: int = 0, stdout: int = 1):
        self.stdin = stdin
        self.stdout = stdout
        # FIXME: Should check if stdin/stdout is tty and read/flush appropriately.
        self.in_alternate_screen: bool = False
        self._event_buffer: list[Event] = []
        self._event_handler: Callable[[list[Event]], None] | None = None
        self._escape_timeout: asyncio.TimerHandle | None = None
        self._dsr_timeouts: dict[bytes, asyncio.TimerHandle] = {}

    cdef void add_event(self, event: Event):
        self.in_buf.len = 0
        self.state = GROUND
        self._event_buffer.append(event)

    cdef void feed1(self, uint8 char_):
        if fbuf_put_char(&self.in_buf, char_):
            raise MemoryError
        cdef bytes data

        if self.state == OSC:
            if fbuf_endswith(&self.in_buf, STRING_TERMINATOR, 2):
                self.execute_osc()
        elif self.state == PASTE:
            # Gross \r handling...
            # Replace \r with \n, but skip \n if \r\n.
            if char_ == 0xd:
                self.in_buf.buf[self.in_buf.len - 1] = 0xa
                self.skip_newline = 1
            elif self.skip_newline:
                self.skip_newline = 0
                if char_ == 0xa:
                    self.in_buf.len -= 1
                    return
            if fbuf_endswith(&self.in_buf, PASTE_END, 6):
                data = self.in_buf.buf[:self.in_buf.len - 6]
                self.add_event(PasteEvent(data.decode()))
        elif char_ == 0x1b:
            self.state = ESCAPE
            self.in_buf.buf[0] = 0x1b
            self.in_buf.len = 1
        elif self.state == GROUND:
            data = <bytes>char_
            if 0x20 <= char_ < 0x7f:
                data = <bytes>char_
                self.add_event(KeyEvent(data.decode()))
            else:
                self.execute_ansi_escapes()
        elif self.state == EXECUTE_NEXT:
            self.execute_ansi_escapes()
        elif self.state == DECRPM:
            self.execute_decrpm()
        elif self.state == ESCAPE:
            if char_ == 0x5b:
                self.state = CSI
            elif char_ == 0x4f:
                self.state = EXECUTE_NEXT
            elif char_ == 0x5d:
                self.state = OSC
            elif 0x20 <= char_ < 0x7f:
                data = <bytes>char_
                self.add_event(KeyEvent(data.decode(), alt=True))
            else:
                self.execute_ansi_escapes()
        elif self.state == CSI:
            if char_ == 0x5b:
                self.state = EXECUTE_NEXT
            elif 0x30 <= char_ <= 0x3f and char_ != 0x3a:
                self.state = CSI_PARAMS
            else:
                self.execute_csi()
        elif self.state is CSI_PARAMS:
            if char_ == 0x24:
                self.state = DECRPM
            elif char_ < 0x30 or char_ > 0x39 and char_ != 0x3b:
                self.execute_csi_params()

    cdef void execute_ansi_escapes(self):
        cdef bytes escape = self.in_buf.buf[:self.in_buf.len]
        if escape in ANSI_ESCAPES:
            self.add_event(KeyEvent(*ANSI_ESCAPES[escape]))
        else:
            self.add_event(UnknownEscapeSequence(escape))

    cdef void execute_csi(self):
        if fbuf_equals(&self.in_buf, FOCUS_IN, 3):
            self.add_event(FocusEvent("in"))
        elif fbuf_equals(&self.in_buf, FOCUS_OUT, 3):
            self.add_event(FocusEvent("out"))
        else:
            self.execute_ansi_escapes()

    cdef void execute_csi_params(self):
        if fbuf_equals(&self.in_buf, PASTE_START, 6):
            self.state = PASTE
            self.skip_newline = 0
            self.in_buf.len = 0
            return

        cdef:
            char initial = 0x0, final = 0x0
            uint[MAX_PARAMS] params
            int nparams = csi_params(&self.in_buf, &initial, &final, &params[0])

        cdef bytes escape
        if nparams < 0:
            escape = self.in_buf.buf[:self.in_buf.len]
            self.add_event(UnknownEscapeSequence(escape))
            return

        if self._dsr_timeouts:
            if initial == 0x0 and final == b"R" and nparams == 2:
                self.add_event(CursorPositionReportEvent(params[0] - 1, params[1] - 1))
                timeout = self._dsr_timeouts.pop(b"\x1b[6n", None)
                if timeout is not None:
                    timeout.cancel()
                return

            if initial == b"?" and final == b"c":
                self.add_event(
                    DeviceAttributesReportEvent(
                        frozenset(int(param) for param in params[:nparams])
                    )
                )
                timeout = self._dsr_timeouts.pop(b"\x1b[c", None)
                if timeout is not None:
                    timeout.cancel()
                return

            if (
                initial == 0x0
                and final == b"t"
                and nparams == 3
                and (params[0] == 4 or params[0] == 6)
            ):
                self.pixel_geometry_reported = 1
                self.add_event(
                    PixelGeometryReportEvent(
                        "terminal" if params[0] == 4 else "cell",
                        Size(params[1], params[2]),
                    )
                )
                if params[0] == 4:
                    timeout = self._dsr_timeouts.pop(b"\x1b[14t", None)
                else:
                    timeout = self._dsr_timeouts.pop(b"\x1b[16t", None)
                if timeout is not None:
                    timeout.cancel()
                return

        if initial == b"<" and (final == b"m" or final == b"M") and nparams == 3:
            self.execute_mouse(&params[0], final)
        else:
            self.execute_ansi_escapes()

    cdef void execute_mouse(self, uint *params, char state):
        cdef:
            uint info = params[0], x = params[1] - 1, y = params[2] - 1
            uint info_button = info % 4
            int dy = y - self.last_y, dx = x - self.last_x
            str button, event_type

        self.last_y = y
        self.last_x = x

        if info_button == 0:
            button = "left"
        elif info_button == 1:
            button = "middle"
        elif info_button == 2:
            button = "right"
        else:
            button = "no button"

        if info & 64:
            if info & 1:
                event_type = "scroll_down"
            else:
                event_type = "scroll_up"
            button = "no button"
        elif info & 32:
            event_type = "mouse_move"
        elif state == b"m":
            event_type = "mouse_up"
        elif button == "no_button":
            event_type = "mouse_move"
        else:
            event_type = "mouse_down"

        self.add_event(
            MouseEvent(
                Point(y, x),
                button,
                event_type,
                bool(info & 8),
                bool(info & 16),
                bool(info & 4),
                dy,
                dx,
            )
        )

    cdef void execute_osc(self):
        cdef:
            bytes escape = self.in_buf.buf[:self.in_buf.len]
            bytes kind, r, g, b

        if self._dsr_timeouts and (color := COLOR_RE.fullmatch(escape)):
            kind, r, g, b = color.groups()
            self.add_event(ColorReportEvent(
                "fg" if kind == b"0" else "bg",
                Color.from_hex(f"{r.decode()}{g.decode()}{b.decode()}"),
            ))
            if kind == b"0":
                timeout = self._dsr_timeouts.pop(b"\x1b]10;?\x1b\\", None)
            else:
                timeout = self._dsr_timeouts.pop(b"\x1b]11;?\x1b\\", None)
            if timeout is not None:
                timeout.cancel()
        else:
            self.add_event(UnknownEscapeSequence(escape))

    cdef void execute_decrpm(self):
        cdef:
            char initial = 0x0, final = 0x0
            uint[MAX_PARAMS] params
            int nparams = csi_params(&self.in_buf, &initial, &final, &params[0])
            uint mode = params[0], value = params[1]
            cdef bytes escape

        if nparams < 0 or not self._dsr_timeouts or mode not in DEC_MODES:
            escape = self.in_buf.buf[:self.in_buf.len]
            self.add_event(UnknownEscapeSequence(escape))
        else:
            timeout = self._dsr_timeouts.pop(b"\x1b[%d$p" % mode, None)
            if timeout is not None:
                timeout.cancel()
            if mode == 1016:
                if initial == 0x0:
                    self.sgr_pixels_supported = value
                elif initial == 0x3f:  # Request to turn on pixel mode.
                    self.pixel_mouse_mode = value
            elif mode == 2026:
                self.sum_supported = value
            self.add_event(DECReplyModeEvent(mode, value))

    def _timeout_escape(self) -> None:
        if self.state != PASTE:
            self.execute_ansi_escapes()

            if self._event_handler is not None:
                self._event_handler(self.events())
            return

        # Timed out during a paste. Check if PASTE_END was cutoff and remove it.
        cdef uint start
        if self.in_buf.len < 6:
            start = self.in_buf.len
        else:
            start = 6

        cdef uint i
        for i in range(start, 0, -1):
            if self.in_buf.buf[self.in_buf.len - i] == 0x1b:
                if fbuf_endswith(&self.in_buf, PASTE_END, i):
                    self.in_buf.len -= i
                break
        cdef bytes data = self.in_buf.buf[:self.in_buf.len]
        self.in_buf.len = 0
        self.add_event(PasteEvent(data.decode()))

        if self._event_handler is not None:
            self._event_handler(self.events())

    cdef void dsr_request(self, escape: bytes):
        if escape in self._dsr_timeouts:
            # Already waiting for terminal response.
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # Not monitoring stdin anyway.
            return

        self._dsr_timeouts[escape] = loop.call_later(
            DSR_REQUEST_TIMEOUT, self._create_dsr_timeout_callback(escape)
        )
        self.write(escape)
        self.flush()

    def _create_dsr_timeout_callback(self, escape: bytes) -> Callable[[], None]:
        def _on_timeout():
            if escape in self._dsr_timeouts:
                del self._dsr_timeouts[escape]
        return _on_timeout

    cpdef void process_stdin(self):
        if self._escape_timeout is not None:
            self._escape_timeout.cancel()
            self._escape_timeout = None

        cdef int[2] size_event
        size_event[0] = -1
        cdef ssize_t read_result = fbuf_read_fd(
            &self.read_buf, self.stdin, &size_event[0]
        )
        if read_result < 0:
            raise OSError("Error reading fd.")
        elif read_result > 0:
            raise MemoryError

        if size_event[0] != -1:
            self.add_event(ResizeEvent(Size(size_event[0], size_event[1])))

        cdef size_t i
        for i in range(self.read_buf.len):
            self.feed1(self.read_buf.buf[i])
        self.read_buf.len = 0

        if self.state == GROUND:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            self._escape_timeout = loop.call_later(ESCAPE_TIMEOUT, self._timeout_escape)

    def raw_mode(self) -> None:
        pass

    def restore_console(self) -> None:
        pass

    def attach(self, event_handler: Callable[[list[Event]], None]) -> None:
        pass

    def unattach(self) -> None:
        pass

    def feed(self, input_: bytes, reset_before: bool = True) -> list[Event]:
        if reset_before:
            if self._escape_timeout is not None:
                self._escape_timeout.cancel()
                self._escape_timeout = None

            self.state = GROUND
            self.in_buf.len = 0
            self._event_buffer.clear()

        for char_ in input_:
            self.feed1(char_)

        if self.state != GROUND:
            self.execute_ansi_escapes()

        return self.events()

    def events(self) -> list[Event]:
        events = self._event_buffer
        self._event_buffer = []
        return events

    def get_size(self) -> Size:
        cols, rows = os.get_terminal_size()
        return Size(rows, cols)

    def write(self, escape: bytes) -> None:
        if fbuf_putn(&self.out_buf, escape, len(escape)):
            raise MemoryError

    def flush(self) -> None:
        if fbuf_flush_fd(&self.out_buf, self.stdout):
            OSError("Failed to flush.")

    def set_title(self, title: str) -> None:
        self.write(b"\x1b]2;%b\x07" % title.encode())

    def enter_alternate_screen(self) -> None:
        self.write(b"\x1b[?1049h\x1b[H")
        self.in_alternate_screen = True

    def exit_alternate_screen(self) -> None:
        self.write(b"\x1b[?1049l")
        self.in_alternate_screen = False

    def enable_mouse_support(self) -> None:
        self.write(
            b"\x1b[?1000h"  # SET_VT200_MOUSE
            b"\x1b[?1003h"  # SET_ANY_EVENT_MOUSE
            b"\x1b[?1006h"  # SET_SGR_EXT_MODE_MOUSE
        )

    def disable_mouse_support(self) -> None:
        self.write(
            b"\x1b[?1000l"  # SET_VT200_MOUSE
            b"\x1b[?1003l"  # SET_ANY_EVENT_MOUSE
            b"\x1b[?1006l"  # SET_SGR_EXT_MODE_MOUSE
        )

    def can_sgr_pixels(self) -> bool:
        return self.pixel_geometry_reported and self.sgr_pixels_supported

    def enable_sgr_pixels(self) -> None:
        self.dsr_request(b"\xb1[?1016h")

    def disable_sgr_pixels(self) -> None:
        self.dsr_request(b"\xb1[?1016l")

    def reset_attributes(self) -> None:
        self.write(b"\x1b[0m")

    def enable_bracketed_paste(self) -> None:
        self.write(b"\x1b[?2004h")

    def disable_bracketed_paste(self) -> None:
        self.write(b"\x1b[?2004l")

    def show_cursor(self) -> None:
        self.write(b"\x1b[?25h")

    def hide_cursor(self) -> None:
        self.write(b"\x1b[?25l")

    def enable_reporting_focus(self) -> None:
        self.write(b"\x1b[?1004h")

    def disable_reporting_focus(self) -> None:
        self.write(b"\x1b[?1004l")

    def expect_dsr(self) -> bool:
        return bool(self._dsr_timeouts)

    def request_cursor_position_report(self) -> None:
        self.dsr_request(b"\x1b[6n")

    def request_foreground_color(self) -> None:
        self.dsr_request(b"\x1b]10;?\x1b\\")

    def request_background_color(self) -> None:
        self.dsr_request(b"\x1b]11;?\x1b\\")

    def request_device_attributes(self) -> None:
        self.dsr_request(b"\x1b[c")

    def request_pixel_geometry(self) -> None:
        self.dsr_request(b"\x1b[16t")

    def request_terminal_geometry(self) -> None:
        self.dsr_request(b"\x1b[14t")

    def request_sgr_pixels_supported(self) -> None:
        # DECRQM 1016
        self.dsr_request(b"\x1b[1016$p")

    def request_synchronized_update_mode_supported(self) -> None:
        # DECRQM 2026
        self.dsr_request(b"\x1b[2026$p")

    def move_cursor(self, pos: Point) -> None:
        y, x = pos
        self.write(b"\x1b[%d;%dH" % (y + 1, x + 1))

    def erase_in_display(self, n: Literal[0, 1, 2, 3] = 0) -> None:
        self.write(b"\x1b[%dJ" % n)
