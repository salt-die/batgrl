"""
Vt100 input for Posix systems.
"""
import sys
import termios
import tty
from asyncio import get_event_loop
from contextlib import contextmanager

from .console_input import read_keys

__all__ = (
    "attach",
    "raw_mode",
    "read_keys",
)

@contextmanager
def attach(callback):
    """
    Context manager that makes this input active in the current event loop.
    """
    stdin = sys.stdin.fileno()

    loop = get_event_loop()
    loop.add_reader(stdin, callback)

    try:
        yield

    finally:
        loop.remove_reader(stdin)

@contextmanager
def raw_mode():
    stdin = sys.stdin.fileno()
    attrs_before = termios.tcgetattr(stdin)

    try:
        attrs_raw = termios.tcgetattr(stdin)

        attrs_raw[tty.LFLAG] &= ~(
            termios.ECHO
            | termios.ICANON
            | termios.IEXTEN
            | termios.ISIG
        )

        attrs_raw[tty.IFLAG] &= ~(
            termios.IXON
            | termios.IXOFF
            | termios.ICRNL
            | termios.INLCR
            | termios.IGNCR
        )

        attrs_raw[tty.CC][termios.VMIN] = 1

        termios.tcsetattr(stdin, termios.TCSANOW, attrs_raw)

        yield

    finally:
        termios.tcsetattr(stdin, termios.TCSANOW, attrs_before)
