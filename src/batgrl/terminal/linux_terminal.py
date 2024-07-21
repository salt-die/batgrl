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

    def events(self) -> list[Event]:
        """Return events from VT100 input stream."""
        reads = []
        while select.select([STDIN], [], [], 0)[0]:
            try:
                read = os.read(STDIN, 1024)
            except OSError:
                break
            else:
                reads.append(read)

        data = b"".join(reads).decode(errors="surrogateescape")
        self.feed(data)

        events = self._events
        self._events = []
        return events

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

    def attach(self, dispatch_events: Callable[[list[Event]], None]) -> None:
        """Dispatch events through ``dispatch_events`` whenever stdin has data."""
        self._event_dispatcher = dispatch_events
        self._events.clear()

        def process():
            dispatch_events(self.events())

        loop = asyncio.get_running_loop()
        loop.add_reader(STDIN, process)

        def on_resize(*_):
            self._events.append(ResizeEvent(self.get_size()))
            loop.call_soon_threadsafe(process)

        signal.signal(signal.SIGWINCH, on_resize)

    def unattach(self) -> None:
        """Stop dispatching input events."""
        self._event_dispatcher = None
        loop = asyncio.get_running_loop()
        loop.remove_reader(STDIN)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)
