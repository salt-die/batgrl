"""Vt100 input for Posix systems."""
import asyncio
import os
import signal
import sys
import termios
import tty
from contextlib import contextmanager

from ....geometry import Size
from .console_input import _EVENTS, events

__all__ = [
    "attach",
    "raw_mode",
    "events",
]


@contextmanager
def attach(callback):
    """Context manager that makes this input active in the current event loop."""
    _EVENTS.clear()

    stdin = sys.stdin.fileno()

    loop = asyncio.get_event_loop()
    loop.add_reader(stdin, callback)

    def on_resize(*_):
        w, h = os.get_terminal_size()
        # Create a size event and schedule event handler:
        _EVENTS.append(Size(h, w))
        loop.call_soon_threadsafe(callback)

    signal.signal(signal.SIGWINCH, on_resize)

    try:
        yield

    finally:
        loop.remove_reader(stdin)
        signal.signal(signal.SIGWINCH, signal.SIG_DFL)


@contextmanager
def raw_mode():
    """Put terminal into raw mode."""
    stdin = sys.stdin.fileno()
    attrs_before = termios.tcgetattr(stdin)
    attrs_raw = termios.tcgetattr(stdin)
    attrs_raw[tty.LFLAG] &= ~(
        termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG
    )
    attrs_raw[tty.IFLAG] &= ~(
        termios.IXON | termios.IXOFF | termios.ICRNL | termios.INLCR | termios.IGNCR
    )
    attrs_raw[tty.CC][termios.VMIN] = 1

    try:
        termios.tcsetattr(stdin, termios.TCSANOW, attrs_raw)
        yield

    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, attrs_before)
