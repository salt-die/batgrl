import io
import sys
import termios
import tty
from asyncio import AbstractEventLoop, get_event_loop
from typing import (
    Callable,
    ContextManager,
    Dict,
    Generator,
    List,
    Optional,
    Set,
    TextIO,
    Tuple,
    Union,
)
from contextlib import contextmanager
from ..key_binding import KeyPress
from .base import Input
from .posix_utils import PosixStdinReader
from .vt100_parser import Vt100Parser

__all__ = [
    "Vt100Input",
    "raw_mode",
]


class Vt100Input(Input):
    """
    Vt100 input for Posix systems.
    (This uses a posix file descriptor that can be registered in the event loop.)
    """

    def __init__(self):
        self.stdin = stdin = sys.stdin
        self._fileno = stdin.fileno()

        self._buffer: List[KeyPress] = []  # Buffer to collect the Key objects.
        self.stdin_reader = PosixStdinReader(self._fileno, encoding=stdin.encoding)
        self.vt100_parser = Vt100Parser(lambda key: self._buffer.append(key))

    @contextmanager
    def attach(self, callback):
        loop = get_event_loop()
        fd = self.fileno()

        def callback_wrapper():
            if self.closed:
                loop.remove_reader(fd)
            callback()

        loop.add_reader(fd, callback_wrapper)

        try:
            yield
        finally:
            loop.remove_reader(fd)

    def read_keys(self) -> List[KeyPress]:
        "Read list of KeyPress."
        # Read text from stdin.
        data = self.stdin_reader.read()

        # Pass it through our vt100 parser.
        self.vt100_parser.feed(data)

        # Return result.
        result = self._buffer
        self._buffer = []
        return result

    def flush_keys(self) -> List[KeyPress]:
        """
        Flush pending keys and return them.
        (Used for flushing the 'escape' key.)
        """
        # Flush all pending keys. (This is most important to flush the vt100
        # 'Escape' key early when nothing else follows.)
        self.vt100_parser.flush()

        # Return result.
        result = self._buffer
        self._buffer = []
        return result

    @property
    def closed(self) -> bool:
        return self.stdin_reader.closed

    @contextmanager
    def raw_mode(self):
        fileno = self.stdin.fileno()

        try:
            attrs_before = termios.tcgetattr(fileno)
        except termios.error:
            attrs_before = None

        try:
            try:
                newattr = termios.tcgetattr(fileno)
            except termios.error:
                pass
            else:
                newattr[tty.LFLAG] = newattr[tty.LFLAG] & ~(
                    termios.ECHO |
                    termios.ICANON |
                    termios.IEXTEN |
                    termios.ISIG
                )
                newattr[tty.IFLAG] = newattr[tty.IFLAG] & ~(
                    termios.IXON
                    | termios.IXOFF
                    | termios.ICRNL
                    | termios.INLCR
                    | termios.IGNCR
                )

                newattr[tty.CC][termios.VMIN] = 1

                termios.tcsetattr(fileno, termios.TCSANOW, newattr)

            yield

        finally:
            if attrs_before is not None:
                try:
                    termios.tcsetattr(fileno, termios.TCSANOW, attrs_before)
                except termios.error:
                    pass

    def fileno(self) -> int:
        return self.stdin.fileno()
