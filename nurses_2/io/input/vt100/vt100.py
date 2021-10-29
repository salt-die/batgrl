import sys
import termios
import tty
from asyncio import get_event_loop
from contextlib import contextmanager

from .vt100_reader import Vt100Reader


class Vt100Input:
    """
    Vt100 input for Posix systems.
    """
    def __init__(self):
        self.vt100_reader = Vt100Reader()

    @contextmanager
    def attach(self, callback):
        """
        Context manager that makes this input active in the current event loop.
        """
        fileno = sys.stdin.fileno()

        loop = get_event_loop()
        loop.add_reader(fileno, callback)

        try:
            yield

        finally:
            loop.remove_reader(fileno)

    @contextmanager
    def raw_mode(self):
        fileno = sys.stdin.fileno()

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
                    termios.ECHO
                    | termios.ICANON
                    | termios.IEXTEN
                    | termios.ISIG
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

    def read_keys(self):
        """
        Read keys from stdin.
        """
        return self.vt100_reader.read_keys()
