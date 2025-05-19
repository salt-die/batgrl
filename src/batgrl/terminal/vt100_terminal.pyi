"""Base for VT100 terminals."""

from collections.abc import Callable
from typing import Literal

from ..geometry import Point, Size
from .events import Event

DSR_REQUEST_TIMEOUT: float

class Vt100Terminal:
    """
    Base for VT100 terminals.

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

    stdin: int
    stdout: int
    in_alternate_screen: bool
    _event_handler: Callable[[list[Event]], None] | None
    _event_buffer: list[Event]

    def __init__(self, stdin: int = 0, stdout: int = 1) -> None:
        pass

    def process_stdin(self) -> None:
        """Read from stdin and feed data into input parser to generate events."""

    def raw_mode(self) -> None:
        """Set terminal to raw mode."""

    def restore_console(self) -> None:
        """Restore console to its original mode."""

    def attach(self, event_handler: Callable[[list[Event]], None]) -> None:
        """
        Start generating events from stdin.

        Parameters
        ----------
        event_handler : Callable[[list[Event]], None]
            Callable that handles input events.
        """

    def unattach(self) -> None:
        """Stop generating events from stdin."""

    def feed(self, input_: bytes, reset_before: bool = True) -> list[Event]:
        """
        Write bytes to stdin parser and return generated events.

        Parameters
        ----------
        input_ : bytes
            The bytes to feed to the VT100 parser.
        reset_before : bool, default: True
            Whether to reset the parser state, clear input-buffer, and clear events
            before feeding ``input_``.

        Returns
        -------
        list[Event]
            Events generated from ``input_``.
        """

    def events(self) -> list[Event]:
        """Return a list of input events and reset the event buffer."""

    def get_size(self) -> Size:
        """Get terminal size."""

    def write(self, out: bytes) -> None:
        """Write bytes directly to the out-buffer."""

    def flush(self) -> None:
        """Write out-buffer to output stream and flush."""

    def set_title(self, title: str) -> None:
        """Set terminal title."""

    def enter_alternate_screen(self) -> None:
        """Enter alternate screen buffer."""

    def exit_alternate_screen(self) -> None:
        """Exit alternate screen buffer."""

    def enable_mouse_support(self) -> None:
        """Enable mouse support in terminal."""

    def disable_mouse_support(self) -> None:
        """Disable mouse support in terminal."""

    def enable_sgr_pixels(self) -> None:
        """Enable SGR-PIXELS mouse mode."""

    def reset_attributes(self) -> None:
        """Reset character attributes."""

    def enable_bracketed_paste(self) -> None:
        """Enable bracketed paste in terminal."""

    def disable_bracketed_paste(self) -> None:
        """Disable bracketed paste in terminal."""

    def show_cursor(self) -> None:
        """Show cursor in terminal."""

    def hide_cursor(self) -> None:
        """Hide cursor in terminal."""

    def enable_reporting_focus(self) -> None:
        """Enable reporting terminal focus."""

    def disable_reporting_focus(self) -> None:
        """Disable reporting terminal focus."""

    def request_cursor_position_report(self) -> None:
        """Report current cursor position."""

    def request_foreground_color(self) -> None:
        """Report terminal foreground color."""

    def request_background_color(self) -> None:
        """Report terminal background color."""

    def request_device_attributes(self) -> None:
        """Report device attributes."""

    def request_pixel_geometry(self) -> None:
        """Report pixel geometry per cell."""

    def request_terminal_geometry(self) -> None:
        """Report pixel geometry of terminal."""

    def request_sgr_pixels_supported(self) -> None:
        """Report whether SGR-PIXELS mode is supported."""

    def request_synchronized_update_mode_supported(self) -> None:
        """Report whether synchronized update mode is supported."""

    def expect_dsr(self) -> bool:
        """Return whether a device status report is expected."""

    def move_cursor(self, pos: Point) -> None:
        """
        Move cursor to ``pos``.

        Parameters
        ----------
        pos : Point | None, default: None
            Cursor's new position.
        """

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
