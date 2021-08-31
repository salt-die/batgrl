import sys
import termios
import tty
from asyncio import get_event_loop
from contextlib import contextmanager

from .posix_reader import PosixStdinReader
from .vt100_parser import Vt100Parser


class Vt100Input:
    """
    Vt100 input for Posix systems.
    (This uses a posix file descriptor that can be registered in the event loop.)
    """

    def __init__(self):
        self.stdin = sys.stdin
        self._fileno = self.stdin.fileno()

        self._buffer = [ ]  # Buffer to collect the Key objects.
        self.stdin_reader = PosixStdinReader(self._fileno)
        self.vt100_parser = Vt100Parser(lambda key: self._buffer.append(key))

    @contextmanager
    def attach(self, callback):
        fd = self.fileno()

        loop = get_event_loop()
        loop.add_reader(fd, callback)

        try:
            yield

        finally:
            loop.remove_reader(fd)

    def read_keys(self):
        """
        Read keys from stdin.
        """
        data = self.stdin_reader.read()

        self.vt100_parser.feed(data)

        result = self._buffer
        self._buffer = [ ]
        return result

    def flush_keys(self):
        """
        Flush pending keys and return them.
        (Used for flushing the 'escape' key.)
        """
        self.vt100_parser.flush()

        result = self._buffer
        self._buffer = [ ]
        return result

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
