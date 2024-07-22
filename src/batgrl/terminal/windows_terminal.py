"""A windows VT100 terminal."""

import asyncio
from collections.abc import Callable
from ctypes import Structure, Union, byref, windll
from ctypes.wintypes import BOOL, CHAR, DWORD, HANDLE, LONG, LPVOID, SHORT, WCHAR
from typing import Final

from ..geometry import Size
from .events import Event, ResizeEvent
from .vt100_terminal import Vt100Terminal

STDIN = windll.kernel32.GetStdHandle(DWORD(-10))
STDOUT = windll.kernel32.GetStdHandle(DWORD(-11))
KEY_EVENT: Final[int] = 1
WINDOW_BUFFER_SIZE_EVENT: Final[int] = 4
# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200


class UNICODE_OR_ASCII(Union):
    """Windows character."""

    _fields_ = [("AsciiChar", CHAR), ("UnicodeChar", WCHAR)]


class KEY_EVENT_RECORD(Structure):
    """
    Windows key event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684166(v=vs.85).aspx
    """

    _fields_ = [
        ("KeyDown", LONG),
        ("RepeatCount", SHORT),
        ("VirtualKeyCode", SHORT),
        ("VirtualScanCode", SHORT),
        ("uChar", UNICODE_OR_ASCII),
        ("ControlKeyState", LONG),
    ]


class COORD(Structure):
    """
    Windows coord struct.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms682119(v=vs.85).aspx
    """

    _fields_ = [("X", SHORT), ("Y", SHORT)]


class MOUSE_EVENT_RECORD(Structure):
    """
    Windows mouse event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684239(v=vs.85).aspx
    """

    _fields_ = [
        ("MousePosition", COORD),
        ("ButtonState", LONG),
        ("ControlKeyState", LONG),
        ("EventFlags", LONG),
    ]


class WINDOW_BUFFER_SIZE_RECORD(Structure):
    """
    Windows buffer size record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms687093(v=vs.85).aspx
    """

    _fields_ = [("Size", COORD)]


class MENU_EVENT_RECORD(Structure):
    """
    Windows menu event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684213(v=vs.85).aspx
    """

    _fields_ = [("CommandId", LONG)]


class FOCUS_EVENT_RECORD(Structure):
    """
    Windows focus event record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683149(v=vs.85).aspx
    """

    _fields_ = [("SetFocus", LONG)]


class EVENT_RECORD(Union):
    """Windows event record."""

    _fields_ = [
        ("KeyEvent", KEY_EVENT_RECORD),
        ("MouseEvent", MOUSE_EVENT_RECORD),
        ("WindowBufferSizeEvent", WINDOW_BUFFER_SIZE_RECORD),
        ("MenuEvent", MENU_EVENT_RECORD),
        ("FocusEvent", FOCUS_EVENT_RECORD),
    ]


class INPUT_RECORD(Structure):
    """
    Windows input record.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/ms683499(v=vs.85).aspx
    """

    _fields_ = [("EventType", SHORT), ("Event", EVENT_RECORD)]


class SECURITY_ATTRIBUTES(Structure):
    """
    Windows security attributes.

    References
    ----------
    http://msdn.microsoft.com/en-us/library/windows/desktop/aa379560(v=vs.85).aspx
    """

    _fields_ = [
        ("nLength", DWORD),
        ("lpSecurityDescriptor", LPVOID),
        ("bInheritHandle", BOOL),
    ]


class WindowsTerminal(Vt100Terminal):
    """
    A windows VT100 terminal.

    Attributes
    ----------
    in_alternate_screen : bool
        Whether the alternate screen buffer is enabled.
    last_cursor_position_response : Point
        Last reported cursor position.
    """

    def process_stdin(self) -> None:
        """Read from stdin and feed data into input parser to generate events."""
        nevents = DWORD()
        windll.kernel32.GetNumberOfConsoleInputEvents(STDIN, byref(nevents))
        InputRecordArray = INPUT_RECORD * nevents.value
        input_records = InputRecordArray()
        windll.kernel32.ReadConsoleInputW(
            STDIN, input_records, nevents.value, byref(DWORD())
        )
        chars = []
        for input_record in input_records:
            if input_record.EventType == KEY_EVENT:
                key_event = input_record.Event.KeyEvent
                if not key_event.KeyDown:
                    continue
                if key_event.ControlKeyState and not key_event.VirtualKeyCode:
                    continue
                chars.append(key_event.uChar.UnicodeChar)
            elif input_record.EventType == WINDOW_BUFFER_SIZE_EVENT:
                self._purge(chars)
                size = input_record.Event.WindowBufferSizeEvent.Size
                self._event_buffer.append(ResizeEvent(Size(size.Y, size.X)))
        self._purge(chars)

    def _purge(self, chars: list[str]):
        data = (
            "".join(chars).encode("utf-16", "surrogatepass").decode("utf-16")
        )  # Merge surrogate pairs.
        chars.clear()
        self._feed(data)

    def raw_mode(self) -> None:
        """Set terminal to raw mode."""
        self._original_output_mode = DWORD()
        windll.kernel32.GetConsoleMode(STDOUT, byref(self._original_output_mode))
        windll.kernel32.SetConsoleMode(
            STDOUT,
            self._original_output_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
        )
        self._original_input_mode = DWORD()
        windll.kernel32.GetConsoleMode(STDIN, byref(self._original_input_mode))
        windll.kernel32.SetConsoleMode(STDIN, ENABLE_VIRTUAL_TERMINAL_INPUT)

    def restore_console(self) -> None:
        """Restore console to its original mode."""
        windll.kernel32.SetConsoleMode(STDIN, self._original_input_mode)
        windll.kernel32.SetConsoleMode(STDOUT, self._original_output_mode)
        del self._original_input_mode, self._original_output_mode

    def attach(self, event_handler: Callable[[list[Event]], None]) -> None:
        """
        Start generating events from stdin.

        Parameters
        ----------
        event_handler : Callable[[list[Event]], None]
            Callable that handles input events.
        """
        self._event_buffer.clear()
        self._event_handler = event_handler
        loop = asyncio.get_running_loop()
        wait_for = windll.kernel32.WaitForMultipleObjects
        self._remove_event = HANDLE(
            windll.kernel32.CreateEventA(
                SECURITY_ATTRIBUTES(), BOOL(True), BOOL(False), None
            )
        )
        EVENTS = (HANDLE * 2)(self._remove_event, STDIN)

        def ready():
            try:
                self.process_stdin()
                event_handler(self.events())
            finally:
                loop.run_in_executor(None, wait)

        def wait():
            if wait_for(2, EVENTS, BOOL(False), DWORD(-1)) == 0:
                windll.kernel32.CloseHandle(self._remove_event)
                del self._remove_event
            else:
                loop.call_soon_threadsafe(ready)

        loop.run_in_executor(None, wait)

    def unattach(self) -> None:
        """Stop generating events from stdin."""
        self._event_handler = None
        windll.kernel32.SetEvent(self._remove_event)


def is_vt100_enabled() -> bool:
    """Return whether VT100 escape sequences are supported."""
    original_mode = DWORD()
    windll.kernel32.GetConsoleMode(STDOUT, byref(original_mode))

    try:
        return bool(
            windll.kernel32.SetConsoleMode(STDOUT, ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        )
    finally:
        windll.kernel32.SetConsoleMode(STDOUT, original_mode)
