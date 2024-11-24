"""A windows VT100 terminal."""

import asyncio
import re
from collections.abc import Callable
from ctypes import Structure, Union, byref, windll
from ctypes.wintypes import BOOL, CHAR, DWORD, HANDLE, LONG, LPVOID, SHORT, WCHAR
from typing import Final

from ..geometry import Size
from .events import Event, ResizeEvent
from .vt100_terminal import Vt100Terminal

CTRL_SPACE_RE: Final = re.compile(r"\x00+")
CTRL_ALT_SPACE_RE: Final = re.compile(r"\x00*\x1b\x00+")
STDIN = windll.kernel32.GetStdHandle(DWORD(-10))
STDOUT = windll.kernel32.GetStdHandle(DWORD(-11))
KEY_EVENT: Final = 1
WINDOW_BUFFER_SIZE_EVENT: Final = 4
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
    expect_dsr()
        Return whether a device status report is expected.
    move_cursor(pos)
        Move cursor to ``pos``.
    erase_in_display(n)
        Clear part of the screen.
    """

    def _feed(self, data: str) -> None:
        # Some versions of Windows Terminal generate spurious null characters for a few
        # input events. For instance, ctrl+" " generates 3 null characters instead of 1
        # and paste events generate a null character before each "shifted" character.
        # For most inputs, null characters can just be ignored.

        # ! The first two conditions assume the sequences for these events appear fully
        # ! and alone in stdin. Most of the time, key events occur slowly enough for
        # ! this to be true. Failing on other cases is acceptable here to keep this
        # ! logic simple.
        if CTRL_SPACE_RE.fullmatch(data):
            super()._feed("\x00")
        elif CTRL_ALT_SPACE_RE.fullmatch(data):
            super()._feed("\x1b\x00")
        else:
            super()._feed(data.replace("\x00", ""))

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
