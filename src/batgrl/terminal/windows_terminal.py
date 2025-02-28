"""A windows VT100 terminal."""

import asyncio
import msvcrt
from collections.abc import Callable
from ctypes import Structure, byref, windll
from ctypes.wintypes import BOOL, DWORD, HANDLE, LPVOID

from .events import Event
from .vt100_terminal import Vt100Terminal

# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_VIRTUAL_TERMINAL_INPUT = 0x0200


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
    stdin: int
        The stdin file descriptor.
    stdout: int
        The stdout file descriptor.
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
    feed(input_, reset_before)
        Write bytes to stdin parser and return generated events.
    events()
        Return a list of input events and reset the event buffer.
    get_size()
        Get terminal size.
    write(out)
        Write bytes directly to the out-buffer.
    flush()
        Write out-buffer to output stream and flush.
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
    enable_sgr_pixels()
        Enable SGR-PIXELS mouse mode.
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
    request_sgr_pixels_supported()
        Report whether SGR-PIXELS mouse mode is supported.
    request_synchronized_update_mode_supported()
        Report whether synchronized update mode is supported.
    expect_dsr()
        Return whether a device status report is expected.
    move_cursor(pos)
        Move cursor to ``pos``.
    erase_in_display(n)
        Clear part of the screen.
    """

    def __init__(self, stdin: int = 0, stdout: int = 1) -> None:
        super().__init__(stdin, stdout)
        self._original_input_mode = DWORD()
        """Original console input mode."""
        self._stdin_handle = msvcrt.get_osfhandle(stdin)
        self._stdout_handle = msvcrt.get_osfhandle(stdout)

        windll.kernel32.GetConsoleMode(
            self._stdin_handle, byref(self._original_input_mode)
        )

        self._original_output_mode = DWORD()
        """Original console output mode."""
        windll.kernel32.GetConsoleMode(
            self._stdout_handle, byref(self._original_output_mode)
        )

        self._original_input_cp = windll.kernel32.GetConsoleCP()
        """Original console input code page."""
        self._original_output_cp = windll.kernel32.GetConsoleOutputCP()
        """Original console output code page."""

    def raw_mode(self) -> None:
        """Set terminal to raw mode."""
        windll.kernel32.SetConsoleMode(
            self._stdin_handle, ENABLE_VIRTUAL_TERMINAL_INPUT
        )
        windll.kernel32.SetConsoleMode(
            self._stdout_handle,
            self._original_output_mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING,
        )
        windll.kernel32.SetConsoleCP(65001)
        windll.kernel32.SetConsoleOutputCP(65001)

    def restore_console(self) -> None:
        """Restore console to its original mode."""
        windll.kernel32.SetConsoleMode(self._stdin_handle, self._original_input_mode)
        windll.kernel32.SetConsoleMode(self._stdout_handle, self._original_output_mode)
        windll.kernel32.SetConsoleCP(self._original_input_cp)
        windll.kernel32.SetConsoleOutputCP(self._original_output_cp)

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
        self._remove_event = remove_event = HANDLE(
            windll.kernel32.CreateEventA(
                SECURITY_ATTRIBUTES(), BOOL(True), BOOL(False), None
            )
        )
        loop = asyncio.get_running_loop()
        wait_for = windll.kernel32.WaitForMultipleObjects
        EVENTS = (HANDLE * 2)(remove_event, self._stdin_handle)

        def ready():
            try:
                self.process_stdin()
                if self._event_handler is not None:
                    self._event_handler(self.events())
            finally:
                try:
                    loop.run_in_executor(None, wait)
                except RuntimeError:
                    windll.kernel32.CloseHandle(remove_event)

        def wait():
            if wait_for(2, EVENTS, BOOL(False), DWORD(-1)) == 0:
                windll.kernel32.CloseHandle(remove_event)
            else:
                loop.call_soon_threadsafe(ready)

        loop.run_in_executor(None, wait)

    def unattach(self) -> None:
        """Stop generating events from stdin."""
        self._event_handler = None
        windll.kernel32.SetEvent(self._remove_event)
