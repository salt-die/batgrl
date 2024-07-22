"""A linux VT100 terminal."""

import asyncio
import os
import select
import signal
import sys
import termios
import tty
from collections.abc import Callable
from typing import Final

from .events import Event, ResizeEvent
from .vt100_terminal import Vt100Terminal

STDIN: Final[int] = sys.stdin.fileno()


class LinuxTerminal(Vt100Terminal):
    """
    A linux VT100 terminal.

    Attributes
    ----------
    in_alternate_screen : bool
        Whether the alternate screen buffer is enabled.
    last_cursor_position_response : Point
        Last reported cursor position.
    """

    def process_stdin(self) -> None:
        """Read from stdin and feed data into input parser to generate events."""
        reads = []
        while select.select([STDIN], [], [], 0)[0]:
            try:
                read = os.read(STDIN, 1024)
            except OSError:
                break
            else:
                reads.append(read)

        data = b"".join(reads).decode(errors="surrogateescape")
        self._feed(data)

    def raw_mode(self) -> None:
        """Set terminal to raw mode."""
        self._original_mode = termios.tcgetattr(STDIN)
        attrs_raw = termios.tcgetattr(STDIN)
        attrs_raw[tty.LFLAG] &= ~(
            termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG
        )
        attrs_raw[tty.IFLAG] &= ~(
            termios.IXON | termios.IXOFF | termios.ICRNL | termios.INLCR | termios.IGNCR
        )
        attrs_raw[tty.CC][termios.VMIN] = 1
        termios.tcsetattr(STDIN, termios.TCSANOW, attrs_raw)

    def restore_console(self) -> None:
        """Restore console to its original mode."""
        termios.tcsetattr(STDIN, termios.TCSANOW, self._original_mode)
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
            event_handler(self.events())

        loop = asyncio.get_running_loop()
        loop.add_reader(STDIN, process)

        def on_resize(*_):
            self._event_buffer.append(ResizeEvent(self.get_size()))
            loop.call_soon_threadsafe(process)

        signal.signal(signal.SIGWINCH, on_resize)

    def unattach(self) -> None:
        """Stop generating events from stdin."""
        self._event_handler = None
        loop = asyncio.get_running_loop()
        loop.remove_reader(STDIN)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
