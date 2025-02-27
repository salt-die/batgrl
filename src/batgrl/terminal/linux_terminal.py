"""A linux VT100 terminal."""

import asyncio
import signal
import termios
import tty
from collections.abc import Callable

from .events import Event, ResizeEvent
from .vt100_terminal import Vt100Terminal


class LinuxTerminal(Vt100Terminal):
    """
    A linux VT100 terminal.

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

    def raw_mode(self) -> None:
        """Set terminal to raw mode."""
        self._original_mode = termios.tcgetattr(self.stdin)
        attrs_raw = termios.tcgetattr(self.stdin)
        attrs_raw[tty.LFLAG] &= ~(
            termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG
        )
        attrs_raw[tty.IFLAG] &= ~(
            termios.IXON | termios.IXOFF | termios.ICRNL | termios.INLCR | termios.IGNCR
        )
        attrs_raw[tty.CC][termios.VMIN] = 1
        termios.tcsetattr(self.stdin, termios.TCSANOW, attrs_raw)

    def restore_console(self) -> None:
        """Restore console to its original mode."""
        termios.tcsetattr(self.stdin, termios.TCSANOW, self._original_mode)
        del self._original_mode

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

        def process():
            self.process_stdin()
            if self._event_handler is not None:
                self._event_handler(self.events())

        loop = asyncio.get_running_loop()
        loop.add_reader(self.stdin, process)

        def on_resize(*_):
            self._event_buffer.append(ResizeEvent(self.get_size()))
            loop.call_soon_threadsafe(process)

        signal.signal(signal.SIGWINCH, on_resize)

    def unattach(self) -> None:
        """Stop generating events from stdin."""
        self._event_handler = None
        loop = asyncio.get_running_loop()
        loop.remove_reader(self.stdin)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
