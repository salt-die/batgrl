import os
import sys
from asyncio import get_event_loop
from contextlib import contextmanager

import msvcrt
from ctypes import windll

from ctypes import Array, pointer
from ctypes.wintypes import DWORD, HANDLE
from typing import (
    Callable,
    ContextManager,
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    TextIO,
)

from ...mouse.mouse_data_structures import *
from ...widgets.widget_data_structures import Point
from ..eventloop.win32 import create_win32_event, wait_for_handle, wait_for_handles
from ..key_binding.key_processor import KeyPress
from ..keys import Keys
from ..win32_types import (
    INPUT_RECORD,
    KEY_EVENT_RECORD,
    MOUSE_EVENT_RECORD,
    STD_INPUT_HANDLE,
    EventTypes,
)
from .ansi_escape_sequences import REVERSE_ANSI_SEQUENCES
from .base import Input


class Win32Input(Input):
    """
    `Input` class that reads from the Windows console.
    """
    def __init__(self):
        self.console_input_reader = ConsoleInputReader()  # ? Can we combine these classes?

    @contextmanager
    def attach(self, callback):
        """
        Context manager that makes this input active in the current event loop.
        """
        handle = self.handle

        try:
            loop = get_event_loop()
            run_in_executor = loop.run_in_executor
            call_soon_threadsafe = loop.call_soon_threadsafe

            remove_event = create_win32_event()

            def ready():
                try:
                    callback()
                finally:
                    run_in_executor(None, wait)

            def wait():
                if wait_for_handles([remove_event, handle]) is remove_event:
                    windll.kernel32.CloseHandle(remove_event)
                    return

                call_soon_threadsafe(ready)

            run_in_executor(None, wait)

            yield

        finally:
            windll.kernel32.SetEvent(remove_event)

    def read_keys(self):
        return list(self.console_input_reader.read())

    def flush(self):
        pass

    @property
    def closed(self):
        return False

    @contextmanager
    def raw_mode(self):
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))
        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))

        try:
            ENABLE_ECHO_INPUT = 0x0004
            ENABLE_LINE_INPUT = 0x0002
            ENABLE_PROCESSED_INPUT = 0x0001

            windll.kernel32.SetConsoleMode(
                handle,
                original_mode.value
                & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT),
            )

            yield

        finally:
            windll.kernel32.SetConsoleMode(handle, original_mode)

    def fileno(self):
        return sys.stdin.fileno()

    def close(self) -> None:
        self.console_input_reader.close()

    @property
    def handle(self) -> HANDLE:
        return self.console_input_reader.handle


class ConsoleInputReader:
    # Keys with character data.
    mappings = {
        b"\x1b": Keys.Escape,
        b"\x00": Keys.ControlSpace,  # Control-Space (Also for Ctrl-@)
        b"\x01": Keys.ControlA,  # Control-A (home)
        b"\x02": Keys.ControlB,  # Control-B (emacs cursor left)
        b"\x03": Keys.ControlC,  # Control-C (interrupt)
        b"\x04": Keys.ControlD,  # Control-D (exit)
        b"\x05": Keys.ControlE,  # Control-E (end)
        b"\x06": Keys.ControlF,  # Control-F (cursor forward)
        b"\x07": Keys.ControlG,  # Control-G
        b"\x08": Keys.ControlH,  # Control-H (8) (Identical to '\b')
        b"\x09": Keys.ControlI,  # Control-I (9) (Identical to '\t')
        b"\x0a": Keys.ControlJ,  # Control-J (10) (Identical to '\n')
        b"\x0b": Keys.ControlK,  # Control-K (delete until end of line; vertical tab)
        b"\x0c": Keys.ControlL,  # Control-L (clear; form feed)
        b"\x0d": Keys.ControlM,  # Control-M (enter)
        b"\x0e": Keys.ControlN,  # Control-N (14) (history forward)
        b"\x0f": Keys.ControlO,  # Control-O (15)
        b"\x10": Keys.ControlP,  # Control-P (16) (history back)
        b"\x11": Keys.ControlQ,  # Control-Q
        b"\x12": Keys.ControlR,  # Control-R (18) (reverse search)
        b"\x13": Keys.ControlS,  # Control-S (19) (forward search)
        b"\x14": Keys.ControlT,  # Control-T
        b"\x15": Keys.ControlU,  # Control-U
        b"\x16": Keys.ControlV,  # Control-V
        b"\x17": Keys.ControlW,  # Control-W
        b"\x18": Keys.ControlX,  # Control-X
        b"\x19": Keys.ControlY,  # Control-Y (25)
        b"\x1a": Keys.ControlZ,  # Control-Z
        b"\x1c": Keys.ControlBackslash,  # Both Control-\ and Ctrl-|
        b"\x1d": Keys.ControlSquareClose,  # Control-]
        b"\x1e": Keys.ControlCircumflex,  # Control-^
        b"\x1f": Keys.ControlUnderscore,  # Control-underscore (Also for Ctrl-hyphen.)
        b"\x7f": Keys.Backspace,  # (127) Backspace   (ASCII Delete.)
    }

    # Keys that don't carry character data.
    keycodes = {
        # Home/End
        33: Keys.PageUp,
        34: Keys.PageDown,
        35: Keys.End,
        36: Keys.Home,
        # Arrows
        37: Keys.Left,
        38: Keys.Up,
        39: Keys.Right,
        40: Keys.Down,
        45: Keys.Insert,
        46: Keys.Delete,
        # F-keys.
        112: Keys.F1,
        113: Keys.F2,
        114: Keys.F3,
        115: Keys.F4,
        116: Keys.F5,
        117: Keys.F6,
        118: Keys.F7,
        119: Keys.F8,
        120: Keys.F9,
        121: Keys.F10,
        122: Keys.F11,
        123: Keys.F12,
    }

    LEFT_ALT_PRESSED = 0x0002
    RIGHT_ALT_PRESSED = 0x0001
    SHIFT_PRESSED = 0x0010
    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    def __init__(self, recognize_paste=True):
        self._fdcon = None
        self.recognize_paste = recognize_paste

        # When stdin is a tty, use that handle, otherwise, create a handle from
        # CONIN$.
        if sys.stdin.isatty():
            self.handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))
        else:
            self._fdcon = os.open("CONIN$", os.O_RDWR | os.O_BINARY)
            self.handle = HANDLE(msvcrt.get_osfhandle(self._fdcon))

    def close(self):
        "Close fdcon."
        if self._fdcon is not None:
            os.close(self._fdcon)

    def read(self):
        """
        Return a list of `KeyPress` instances. It won't return anything when
        there was nothing to read.  (This function doesn't block.)

        http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
        """
        max_count = 2048  # Max events to read at the same time.

        read = DWORD(0)
        arrtype = INPUT_RECORD * max_count
        input_records = arrtype()

        # Check whether there is some input to read. `ReadConsoleInputW` would
        # block otherwise.
        # (Actually, the event loop is responsible to make sure that this
        # function is only called when there is something to read, but for some
        # reason this happened in the asyncio_win32 loop, and it's better to be
        # safe anyway.)
        if not wait_for_handle(self.handle, timeout=0):
            return

        # Get next batch of input event.
        windll.kernel32.ReadConsoleInputW(
            self.handle, pointer(input_records), max_count, pointer(read)
        )

        # First, get all the keys from the input buffer, in order to determine
        # whether we should consider this a paste event or not.
        all_keys = list(self._get_keys(read, input_records))

        # Fill in 'data' for key presses.
        all_keys = [self._insert_key_data(key) for key in all_keys]

        # Correct non-bmp characters that are passed as separate surrogate codes
        all_keys = list(self._merge_paired_surrogates(all_keys))

        if self.recognize_paste and self._is_paste(all_keys):
            gen = iter(all_keys)
            k: Optional[KeyPress]

            for k in gen:
                # Pasting: if the current key consists of text or \n, turn it
                # into a BracketedPaste.
                data = []
                while k and (not isinstance(k.key, Keys) or k.key == Keys.ControlJ):
                    data.append(k.data)
                    try:
                        k = next(gen)
                    except StopIteration:
                        k = None

                if data:
                    yield KeyPress(Keys.BracketedPaste, "".join(data))
                if k is not None:
                    yield k
        else:
            for k2 in all_keys:
                yield k2

    def _insert_key_data(self, key_press: KeyPress) -> KeyPress:
        """
        Insert KeyPress data, for vt100 compatibility.
        """
        if key_press.data:
            return key_press

        if isinstance(key_press.key, Keys):
            data = REVERSE_ANSI_SEQUENCES.get(key_press.key, "")
        else:
            data = ""

        return KeyPress(key_press.key, data)

    def _get_keys(
        self, read: DWORD, input_records: "Array[INPUT_RECORD]"
    ) -> Iterator[KeyPress]:
        """
        Generator that yields `KeyPress` objects from the input records.
        """
        for i in range(read.value):
            ir = input_records[i]

            # Get the right EventType from the EVENT_RECORD.
            # (For some reason the Windows console application 'cmder'
            # [http://gooseberrycreative.com/cmder/] can return '0' for
            # ir.EventType. -- Just ignore that.)
            if ir.EventType in EventTypes:
                ev = getattr(ir.Event, EventTypes[ir.EventType])

                # Process if this is a key event. (We also have mouse, menu and
                # focus events.)
                if type(ev) == KEY_EVENT_RECORD and ev.KeyDown:
                    for key_press in self._event_to_key_presses(ev):
                        yield key_press

                elif type(ev) == MOUSE_EVENT_RECORD:
                    for key_press in self._handle_mouse(ev):
                        yield key_press

    @staticmethod
    def _merge_paired_surrogates(key_presses: List[KeyPress]) -> Iterator[KeyPress]:
        """
        Combines consecutive KeyPresses with high and low surrogates into
        single characters
        """
        buffered_high_surrogate = None
        for key in key_presses:
            is_text = not isinstance(key.key, Keys)
            is_high_surrogate = is_text and "\uD800" <= key.key <= "\uDBFF"
            is_low_surrogate = is_text and "\uDC00" <= key.key <= "\uDFFF"

            if buffered_high_surrogate:
                if is_low_surrogate:
                    # convert high surrogate + low surrogate to single character
                    fullchar = (
                        (buffered_high_surrogate.key + key.key)
                        .encode("utf-16-le", "surrogatepass")
                        .decode("utf-16-le")
                    )
                    key = KeyPress(fullchar, fullchar)
                else:
                    yield buffered_high_surrogate
                buffered_high_surrogate = None

            if is_high_surrogate:
                buffered_high_surrogate = key
            else:
                yield key

        if buffered_high_surrogate:
            yield buffered_high_surrogate

    @staticmethod
    def _is_paste(keys: List[KeyPress]) -> bool:
        """
        Return `True` when we should consider this list of keys as a paste
        event. Pasted text on windows will be turned into a
        `Keys.BracketedPaste` event. (It's not 100% correct, but it is probably
        the best possible way to detect pasting of text and handle that
        correctly.)
        """
        # Consider paste when it contains at least one newline and at least one
        # other character.
        text_count = 0
        newline_count = 0

        for k in keys:
            if not isinstance(k.key, Keys):
                text_count += 1
            if k.key == Keys.ControlM:
                newline_count += 1

        return newline_count >= 1 and text_count > 1

    def _event_to_key_presses(self, ev: KEY_EVENT_RECORD) -> List[KeyPress]:
        """
        For this `KEY_EVENT_RECORD`, return a list of `KeyPress` instances.
        """
        assert type(ev) == KEY_EVENT_RECORD and ev.KeyDown

        result: Optional[KeyPress] = None

        control_key_state = ev.ControlKeyState
        u_char = ev.uChar.UnicodeChar
        # Use surrogatepass because u_char may be an unmatched surrogate
        ascii_char = u_char.encode("utf-8", "surrogatepass")

        # NOTE: We don't use `ev.uChar.AsciiChar`. That appears to be the
        # unicode code point truncated to 1 byte. See also:
        # https://github.com/ipython/ipython/issues/10004
        # https://github.com/jonathanslenders/python-prompt-toolkit/issues/389

        if u_char == "\x00":
            if ev.VirtualKeyCode in self.keycodes:
                result = KeyPress(self.keycodes[ev.VirtualKeyCode], "")
        else:
            if ascii_char in self.mappings:
                if self.mappings[ascii_char] == Keys.ControlJ:
                    u_char = (
                        "\n"  # Windows sends \n, turn into \r for unix compatibility.
                    )
                result = KeyPress(self.mappings[ascii_char], u_char)
            else:
                result = KeyPress(u_char, u_char)

        # First we handle Shift-Control-Arrow/Home/End (need to do this first)
        if (
            (
                control_key_state & self.LEFT_CTRL_PRESSED
                or control_key_state & self.RIGHT_CTRL_PRESSED
            )
            and control_key_state & self.SHIFT_PRESSED
            and result
        ):
            mapping: Dict[str, str] = {
                Keys.Left: Keys.ControlShiftLeft,
                Keys.Right: Keys.ControlShiftRight,
                Keys.Up: Keys.ControlShiftUp,
                Keys.Down: Keys.ControlShiftDown,
                Keys.Home: Keys.ControlShiftHome,
                Keys.End: Keys.ControlShiftEnd,
                Keys.Insert: Keys.ControlShiftInsert,
                Keys.PageUp: Keys.ControlShiftPageUp,
                Keys.PageDown: Keys.ControlShiftPageDown,
            }
            result.key = mapping.get(result.key, result.key)

        # Correctly handle Control-Arrow/Home/End and Control-Insert/Delete keys.
        if (
            control_key_state & self.LEFT_CTRL_PRESSED
            or control_key_state & self.RIGHT_CTRL_PRESSED
        ) and result:
            mapping = {
                Keys.Left: Keys.ControlLeft,
                Keys.Right: Keys.ControlRight,
                Keys.Up: Keys.ControlUp,
                Keys.Down: Keys.ControlDown,
                Keys.Home: Keys.ControlHome,
                Keys.End: Keys.ControlEnd,
                Keys.Insert: Keys.ControlInsert,
                Keys.Delete: Keys.ControlDelete,
                Keys.PageUp: Keys.ControlPageUp,
                Keys.PageDown: Keys.ControlPageDown,
            }
            result.key = mapping.get(result.key, result.key)

        # Turn 'Tab' into 'BackTab' when shift was pressed.
        # Also handle other shift-key combination
        if control_key_state & self.SHIFT_PRESSED and result:
            mapping = {
                Keys.Tab: Keys.BackTab,
                Keys.Left: Keys.ShiftLeft,
                Keys.Right: Keys.ShiftRight,
                Keys.Up: Keys.ShiftUp,
                Keys.Down: Keys.ShiftDown,
                Keys.Home: Keys.ShiftHome,
                Keys.End: Keys.ShiftEnd,
                Keys.Insert: Keys.ShiftInsert,
                Keys.Delete: Keys.ShiftDelete,
                Keys.PageUp: Keys.ShiftPageUp,
                Keys.PageDown: Keys.ShiftPageDown,
            }
            result.key = mapping.get(result.key, result.key)

        # Turn 'Space' into 'ControlSpace' when control was pressed.
        if (
            (
                control_key_state & self.LEFT_CTRL_PRESSED
                or control_key_state & self.RIGHT_CTRL_PRESSED
            )
            and result
            and result.data == " "
        ):
            result = KeyPress(Keys.ControlSpace, " ")

        # Turn Control-Enter into META-Enter. (On a vt100 terminal, we cannot
        # detect this combination. But it's really practical on Windows.)
        if (
            (
                control_key_state & self.LEFT_CTRL_PRESSED
                or control_key_state & self.RIGHT_CTRL_PRESSED
            )
            and result
            and result.key == Keys.ControlJ
        ):
            return [KeyPress(Keys.Escape, ""), result]

        # Return result. If alt was pressed, prefix the result with an
        # 'Escape' key, just like unix VT100 terminals do.

        # NOTE: Only replace the left alt with escape. The right alt key often
        #       acts as altgr and is used in many non US keyboard layouts for
        #       typing some special characters, like a backslash. We don't want
        #       all backslashes to be prefixed with escape. (Esc-\ has a
        #       meaning in E-macs, for instance.)
        if result:
            meta_pressed = control_key_state & self.LEFT_ALT_PRESSED

            if meta_pressed:
                return [KeyPress(Keys.Escape, ""), result]
            else:
                return [result]

        else:
            return []

    def _handle_mouse(self, ev):
        FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
        RIGHTMOST_BUTTON_PRESSED =  0x0002

        RIGHT_ALT_PRESSED = 0x0001
        LEFT_ALT_PRESSED = 0x0002
        RIGHT_CTRL_PRESSED = 0x0004
        LEFT_CTRL_PRESSED = 0x0008
        SHIFT_PRESSED = 0x0010

        MOUSE_MOVED = 0x0001
        MOUSE_WHEELED = 0x0004

        position = Point(ev.MousePosition.Y, ev.MousePosition.X)

        # Event type
        if ev.EventFlags & MOUSE_MOVED:
            event_type = MouseEventType.MOUSE_MOVE
        elif ev.EventFlags & MOUSE_WHEELED:
            if ev.ButtonState > 0:
                event_type = MouseEventType.SCROLL_UP
            else:
                event_type = MouseEventType.SCROLL_DOWN
        elif not ev.ButtonState:
            event_type = MouseEventType.MOUSE_UP
        else:
            event_type = MouseEventType.MOUSE_DOWN

        # Buttons
        if not ev.ButtonState:
            button = MouseButton.NO_BUTTON
        elif ev.ButtonState & FROM_LEFT_1ST_BUTTON_PRESSED:
            button = MouseButton.LEFT
        elif ev.ButtonState & RIGHTMOST_BUTTON_PRESSED:
            button = MouseButton.RIGHT
        # More buttons here:
        #     https://docs.microsoft.com/en-us/windows/console/mouse-event-record-str?redirectedfrom=MSDN
        # For now, just assume middle-mouse button.
        else:
            button = MouseButton.MIDDLE

        # Modifiers
        mods = 0
        if ev.ControlKeyState & LEFT_ALT_PRESSED or ev.ControlKeyState & RIGHT_ALT_PRESSED:
            mods |= MouseModifierKey.ALT
        if ev.ControlKeyState & LEFT_CTRL_PRESSED or ev.ControlKeyState & RIGHT_CTRL_PRESSED:
            mods |= MouseModifierKey.CONTROL
        if ev.ControlKeyState & SHIFT_PRESSED:
            mods |= MouseModifierKey.SHIFT

        modifier = MouseModifier(mods)

        data = MouseEvent(position, event_type, button, modifier)
        return [ KeyPress(Keys.WindowsMouseEvent, data) ]
