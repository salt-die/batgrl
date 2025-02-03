"""Base for VT100 terminals."""

import asyncio
import os
import re
from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import Enum, auto
from io import StringIO
from typing import Final, Literal

from .._fbuf import FBufWrapper
from ..colors import Color
from ..geometry import Point, Size
from .ansi_escapes import ANSI_ESCAPES
from .events import (
    ColorReportEvent,
    CursorPositionReportEvent,
    DeviceAttributesReportEvent,
    Event,
    FocusEvent,
    KeyEvent,
    MouseButton,
    MouseEvent,
    MouseEventType,
    PasteEvent,
    PixelGeometryReportEvent,
    UnknownEscapeSequence,
)

CPR_RE: Final = re.compile(r"\x1b\[(\d+);(\d+)R")
COLOR_RE: Final = re.compile(
    r"\x1b\]1([10]);rgb:([0-9a-f]{4})/([0-9a-f]{4})/([0-9a-f]{4})\x1b\\"
)
# \x1b[?61;4;6;7;14;21;22;23;24;28;32;42c
DEVICE_ATTRIBUTES_RE: Final = re.compile(r"\x1b\[\?[0-9;]+c")
PIXEL_GEOMETRY_RE: Final = re.compile(r"\x1b\[([6|4]);(\d+);(\d+)t")
MOUSE_SGR_RE: Final = re.compile(r"\x1b\[<(\d+);(\d+);(\d+)(m|M)")
PARAMS_RE: Final = re.compile(r"[0-9;]")
BRACKETED_PASTE_START: Final = "\x1b[200~"
BRACKETED_PASTE_END: Final = "\x1b[201~"
FOCUS_IN: Final = "\x1b[I"
FOCUS_OUT: Final = "\x1b[O"
ESCAPE_TIMEOUT: Final = 0.05
"""Time in seconds before escape buffer is reset."""
DRS_REQUEST_TIMEOUT: Final = 0.1
"""
Time in seconds for the input parser to expect a response to a device status report
request.
"""


class ParserState(Enum):
    """State of VT100 input parser."""

    GROUND = auto()
    """Initial state."""
    ESCAPE = auto()
    """Start of an escape sequence."""
    CSI = auto()
    """Start of a control sequence."""
    OSC = auto()
    """Start of an operating system command sequence."""
    PARAMS = auto()
    """Collecting parameters of a control sequence."""
    PASTE = auto()
    """Collecting paste data."""
    EXECUTE_NEXT = auto()
    """Execute escape buffer after receiving next character."""


class Vt100Terminal(ABC):
    """
    Base for VT100 terminals.

    Attributes
    ----------
    in_alternate_screen : bool
        Whether the alternate screen buffer is enabled.

    Methods
    -------
    process_stdin()
        Read from stdin and feed data into input parser to generate events.
    raw_mode()
        Set terminal to raw mode.
    restore_console()
        Restore console to its original mode.
    attach(event_handler)
        Start generating events from stdin.
    unattach()
        Stop generating events from stdin.
    events()
        Return a list of input events and reset the event buffer.
    get_size()
        Get terminal size.
    flush()
        Write buffer to output stream and flush.
    set_title(title)
        Set terminal title.
    enter_alternate_screen()
        Enter alternate screen buffer.
    exit_alternate_screen()
        Exit alternate screen buffer.
    enable_mouse_support()
        Enable mouse support in terminal.
    disable_mouse_support()
        Disable mouse support in terminal.
    reset_attributes()
        Reset character attributes.
    enable_bracketed_paste()
        Enable bracketed paste in terminal.
    disable_bracketed_paste()
        Disable bracketed paste in terminal.
    show_cursor()
        Show cursor in terminal.
    hide_cursor()
        Hide cursor in terminal.
    enable_reporting_focus()
        Enable reporting terminal focus.
    disable_reporting_focus()
        Disable reporting terminal focus.
    request_cursor_position_report()
        Report current cursor position.
    request_foreground_color()
        Report terminal foreground color.
    request_background_color()
        Report terminal background color.
    request_device_attributes()
        Report device attributes.
    request_pixel_geometry()
        Report pixel geometry per cell.
    request_terminal_geometry()
        Report pixel geometry of terminal.
    expect_dsr()
        Return whether a device status report is expected.
    move_cursor(pos)
        Move cursor to ``pos``.
    erase_in_display(n)
        Clear part of the screen.
    """

    def __init__(self):
        self.in_alternate_screen: bool = False
        """Whether the alternate screen buffer is enabled."""
        self._escape_buffer: StringIO | None = None
        """Escape sequence buffer."""
        self._paste_buffer: StringIO | None = None
        """Paste buffer."""
        self._event_buffer: list[Event] = []
        """Events generated during input parsing."""
        self._out_buffer: FBufWrapper = FBufWrapper()
        """
        Output buffer.

        Escapes for stdout are collected here before ``flush()`` is called.
        """
        self._state: ParserState = ParserState.GROUND
        """State of VT100 input parser."""
        self._timeout_escape: asyncio.TimerHandle | None = None
        """Timeout handle for executing escape buffer."""
        self._dsr_pending: int = 0
        """Pending device status report requests."""
        self._last_y: int = 0
        """Last mouse y-coordinate."""
        self._last_x: int = 0
        """Last mouse x-coordinate."""
        self._event_handler: Callable[[list[Event]], None] | None = None
        """Event handler set with ``attach()`` or unset with ``unattach()``."""

    @abstractmethod
    def process_stdin(self) -> None:
        """Read from stdin and feed data into input parser to generate events."""

    @abstractmethod
    def raw_mode(self) -> None:
        """Set terminal to raw mode."""

    @abstractmethod
    def restore_console(self) -> None:
        """Restore console to its original mode."""

    @abstractmethod
    def attach(self, event_handler: Callable[[list[Event]], None]) -> None:
        """
        Start generating events from stdin.

        Parameters
        ----------
        event_handler : Callable[[list[Event]], None]
            Callable that handles input events.
        """

    @abstractmethod
    def unattach(self) -> None:
        """Stop generating events from stdin."""

    def events(self) -> list[Event]:
        """Return a list of input events and reset the event buffer."""
        events = self._event_buffer
        self._event_buffer = []
        return events

    def get_size(self) -> Size:
        """Get terminal size."""
        cols, rows = os.get_terminal_size()
        return Size(rows, cols)

    def _feed(self, data: str) -> None:
        """Generate events from terminal input data."""
        if self._timeout_escape is not None:
            self._timeout_escape.cancel()
            self._timeout_escape = None

        for char in data:
            self._feed1(char)

        if self._state is ParserState.GROUND:
            return

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        else:
            self._timeout_escape = loop.call_later(ESCAPE_TIMEOUT, self._reset_escape)

    def _feed1(self, char: str) -> None:
        """Feed a single character from terminal input into the parser."""
        if self._state is ParserState.OSC:
            self._escape_buffer.write(char)
            if char == "\\" and self._escape_buffer.getvalue().endswith("\x1b\\"):
                self._execute()
        elif self._state is not ParserState.PASTE and char == "\x1b":
            # Start a new escape (possibly canceling previous escape).
            self._escape_buffer = StringIO()
            self._escape_buffer.write(char)
            self._state = ParserState.ESCAPE
        elif self._state is ParserState.EXECUTE_NEXT:
            self._escape_buffer.write(char)
            self._execute()
        elif self._state is ParserState.PASTE:
            self._paste_buffer.write(char)
            if char == "~":
                paste = self._paste_buffer.getvalue()
                if paste.endswith(BRACKETED_PASTE_END):
                    self._event_buffer.append(PasteEvent(paste[:-6]))
                    self._paste_buffer = None
                    self._state = ParserState.GROUND
        elif self._state is ParserState.GROUND:
            if ord(char) < 0x20 or char == "\x7f" or char == "\x9b":
                self._escape_buffer = StringIO()
                self._escape_buffer.write(char)
                self._execute()
            else:
                self._event_buffer.append(KeyEvent(char))
        elif self._state is ParserState.ESCAPE:
            self._escape_buffer.write(char)
            if char == "[":
                self._state = ParserState.CSI
            elif char == "O":
                self._state = ParserState.EXECUTE_NEXT
            elif char == "]":
                self._state = ParserState.OSC
            else:
                self._execute()
        elif self._state is ParserState.CSI:
            self._escape_buffer.write(char)
            if char == "[":
                self._state = ParserState.EXECUTE_NEXT
            elif char == "<" or char == "?":
                self._state = ParserState.PARAMS
            elif PARAMS_RE.fullmatch(char) is None:
                self._execute()
            else:
                self._state = ParserState.PARAMS
        elif self._state is ParserState.PARAMS:
            self._escape_buffer.write(char)
            if PARAMS_RE.fullmatch(char) is None:
                self._execute()

    def _execute(self) -> None:
        """Produce an event from the escape buffer."""
        self._state = ParserState.GROUND
        escape = self._escape_buffer.getvalue()
        self._escape_buffer = None

        if self._dsr_pending and self._execute_dsr_request(escape):
            return
        if escape == BRACKETED_PASTE_START:
            self._state = ParserState.PASTE
            self._paste_buffer = StringIO(newline=None)
        elif escape == FOCUS_IN:
            self._event_buffer.append(FocusEvent("in"))
        elif escape == FOCUS_OUT:
            self._event_buffer.append(FocusEvent("out"))
        elif sgr_match := MOUSE_SGR_RE.fullmatch(escape):
            info = int(sgr_match[1])
            y = int(sgr_match[3]) - 1
            x = int(sgr_match[2]) - 1
            dy = y - self._last_y
            dx = x - self._last_x
            self._last_y = y
            self._last_x = x
            state = sgr_match[4]
            button: MouseButton = ["left", "middle", "right", "no_button"][info % 4]
            event_type: MouseEventType

            if info & 64:
                event_type = "scroll_down" if info & 1 else "scroll_up"
                button = "no_button"
            elif info & 32:
                event_type = "mouse_move"
            elif state == "m":
                event_type = "mouse_up"
            else:
                event_type = "mouse_move" if button == "no_button" else "mouse_down"

            shift = bool(info & 4)
            alt = bool(info & 8)
            ctrl = bool(info & 16)

            self._event_buffer.append(
                MouseEvent(Point(y, x), button, event_type, alt, ctrl, shift, dy, dx)
            )
        elif escape in ANSI_ESCAPES:
            self._event_buffer.append(KeyEvent(*ANSI_ESCAPES[escape]))
        elif len(escape) == 2 and 32 <= ord(escape[1]) <= 126:
            self._event_buffer.append(KeyEvent(escape[1], alt=True))
        else:
            self._event_buffer.append(UnknownEscapeSequence(escape))

    def _execute_dsr_request(self, escape: str) -> bool:
        """Return whether a device status report was issued."""
        event: Event
        if cpr_match := CPR_RE.fullmatch(escape):
            y, x = cpr_match.groups()
            event = CursorPositionReportEvent(Point(int(y) - 1, int(x) - 1))
        elif color_match := COLOR_RE.fullmatch(escape):
            kind, r, g, b = color_match.groups()
            event = ColorReportEvent(
                kind="fg" if kind == "0" else "bg",
                color=Color.from_hex(f"{r[:2]}{g[:2]}{b[:2]}"),
            )
        elif device_attributes_match := DEVICE_ATTRIBUTES_RE.fullmatch(escape):
            device_attributes = device_attributes_match.group()[3:-1].split(";")
            event = DeviceAttributesReportEvent(frozenset(map(int, device_attributes)))
        elif pixel_geometry_match := PIXEL_GEOMETRY_RE.fullmatch(escape):
            kind, height, width = pixel_geometry_match.groups()
            event = PixelGeometryReportEvent(
                kind="cell" if kind == "6" else "terminal",
                geometry=Size(int(height), int(width)),
            )
        else:
            return False

        self._dsr_pending -= 1
        self._event_buffer.append(event)
        return True

    def _reset_escape(self) -> None:
        """Execute escape buffer after a timeout period."""
        if self._state is ParserState.PASTE:
            paste = self._paste_buffer.getvalue()
            self._paste_buffer = None
            self._state = ParserState.GROUND

            # Timed out during a paste. Check if there's a partial escape to remove
            # (maybe BRACKETED_PASTE_END was cutoff).
            partial_escape_index = paste.find("\x1b")
            if partial_escape_index != -1:
                ending = paste[partial_escape_index:]
                if BRACKETED_PASTE_END[: len(ending)] == ending:
                    paste = paste[:partial_escape_index]
            self._event_buffer.append(PasteEvent(paste))
            self._paste_buffer = None
        else:
            self._execute()

        if self._event_handler is not None:
            self._event_handler(self.events())

    def flush(self) -> None:
        """Write buffer to output stream and flush."""
        if not self._out_buffer:
            return

        self._out_buffer.flush()

    def set_title(self, title: str) -> None:
        """Set terminal title."""
        self._out_buffer.write(b"\x1b]2;%b\x07" % title.encode())

    def enter_alternate_screen(self) -> None:
        """Enter alternate screen buffer."""
        self._out_buffer.write(b"\x1b[?1049h\x1b[H")
        self.in_alternate_screen = True

    def exit_alternate_screen(self) -> None:
        """Exit alternate screen buffer."""
        self._out_buffer.write(b"\x1b[?1049l")
        self.in_alternate_screen = False

    def enable_mouse_support(self) -> None:
        """Enable mouse support in terminal."""
        self._out_buffer.write(
            b"\x1b[?1000h"  # SET_VT200_MOUSE
            b"\x1b[?1003h"  # SET_ANY_EVENT_MOUSE
            b"\x1b[?1006h"  # SET_SGR_EXT_MODE_MOUSE
        )

    def disable_mouse_support(self) -> None:
        """Disable mouse support in terminal."""
        self._out_buffer.write(
            b"\x1b[?1000l"  # SET_VT200_MOUSE
            b"\x1b[?1003l"  # SET_ANY_EVENT_MOUSE
            b"\x1b[?1006l"  # SET_SGR_EXT_MODE_MOUSE
        )

    def reset_attributes(self) -> None:
        """Reset character attributes."""
        self._out_buffer.write(b"\x1b[0m")

    def enable_bracketed_paste(self) -> None:
        """Enable bracketed paste in terminal."""
        self._out_buffer.write(b"\x1b[?2004h")

    def disable_bracketed_paste(self) -> None:
        """Disable bracketed paste in terminal."""
        self._out_buffer.write(b"\x1b[?2004l")

    def show_cursor(self) -> None:
        """Show cursor in terminal."""
        self._out_buffer.write(b"\x1b[?25h")

    def hide_cursor(self) -> None:
        """Hide cursor in terminal."""
        self._out_buffer.write(b"\x1b[?25l")

    def enable_reporting_focus(self) -> None:
        """Enable reporting terminal focus."""
        self._out_buffer.write(b"\x1b[?1004h")

    def disable_reporting_focus(self) -> None:
        """Disable reporting terminal focus."""
        self._out_buffer.write(b"\x1b[?1004l")

    def _dsr_request(self, escape: bytes) -> None:
        """Make a device status report request and schedule its cancellation."""
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        self._dsr_pending += 1
        loop.call_later(DRS_REQUEST_TIMEOUT, self._timeout_dsr)
        self._out_buffer.write(escape)
        self.flush()

    def _timeout_dsr(self) -> None:
        if self._dsr_pending:
            self._dsr_pending -= 1

    def request_cursor_position_report(self) -> None:
        """Report current cursor position."""
        self._dsr_request(b"\x1b[6n")

    def request_foreground_color(self) -> None:
        """Report terminal foreground color."""
        self._dsr_request(b"\x1b]10;?\x1b\\")

    def request_background_color(self) -> None:
        """Report terminal background color."""
        self._dsr_request(b"\x1b]11;?\x1b\\")

    def request_device_attributes(self) -> None:
        """Report device attributes."""
        self._dsr_request(b"\x1b[c")

    def request_pixel_geometry(self) -> None:
        """Report pixel geometry per cell."""
        self._dsr_request(b"\x1b[16t")

    def request_terminal_geometry(self) -> None:
        """Report pixel geometry of terminal."""
        self._dsr_request(b"\x1b[14t")

    def expect_dsr(self) -> bool:
        """Return whether a device status report is expected."""
        return bool(self._dsr_pending)

    def move_cursor(self, pos: Point) -> None:
        """
        Move cursor to ``pos``.

        Parameters
        ----------
        pos : Point | None, default: None
            Cursor's new position.
        """
        y, x = pos
        self._out_buffer.write(b"\x1b[%d;%dH" % (y + 1, x + 1))

    def erase_in_display(self, n: Literal[0, 1, 2, 3] = 0) -> None:
        """
        Clear part of the screen.

        Parameters
        ----------
        n : int, default: 0
            Determines which part of the screen to clear. If n is ``0``, clear from
            cursor to end of the screen. If n is ``1``, clear from cursor to beginning
            of the screen. If n is ``2``, clear entire screen. If n is ``3``, clear
            entire screen and delete all lines in scrollback buffer.
        """
        self._out_buffer.write(b"\x1b[%dJ" % n)
