"""
Output for vt100 terminals.

A lot of thanks, regarding outputting of colors, goes to the Pygments project:
(We don't rely on Pygments anymore, because many things are very custom, and
everything has been highly optimized.)
http://pygments.org/
"""
import array
import errno
import io
import os
import sys
from contextlib import contextmanager
from typing import (
    IO,
    Callable,
    Dict,
    Hashable,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Set,
    TextIO,
    Tuple,
    cast,
)

from ...widgets.widget_data_structures import Size
from . import Output
from ..utils import is_dumb_terminal

__all__ = [
    "Vt100_Output",
]


def _get_size(fileno: int) -> Tuple[int, int]:
    """
    Get the size of this pseudo terminal.

    :param fileno: stdout.fileno()
    :returns: A (rows, cols) tuple.
    """
    size = os.get_terminal_size(fileno)
    return size.lines, size.columns


class Vt100_Output(Output):
    """
    :param get_size: A callable which returns the `Size` of the output terminal.
    :param stdout: Any object with has a `write` and `flush` method + an 'encoding' property.
    :param term: The terminal environment variable. (xterm, xterm-256color, linux, ...)
    :param write_binary: Encode the output before writing it. If `True` (the
        default), the `stdout` object is supposed to expose an `encoding` attribute.
    """

    # For the error messages. Only display "Output is not a terminal" once per
    # file descriptor.
    _fds_not_a_terminal: Set[int] = set()

    def __init__(
        self,
        stdout: TextIO,
        get_size: Callable[[], Size],
        term: Optional[str] = None,
        write_binary: bool = True,
        enable_bell: bool = True,
    ) -> None:

        assert all(hasattr(stdout, a) for a in ("write", "flush"))

        if write_binary:
            assert hasattr(stdout, "encoding")

        self._buffer: List[str] = []
        self.stdout: TextIO = stdout
        self.write_binary = write_binary
        self._get_size = get_size
        self.term = term
        self.enable_bell = enable_bell

    @classmethod
    def from_pty(
        cls,
        stdout: TextIO,
        term: Optional[str] = None,
        enable_bell: bool = True,
    ) -> "Vt100_Output":
        """
        Create an Output class from a pseudo terminal.
        (This will take the dimensions by reading the pseudo
        terminal attributes.)
        """
        fd: Optional[int]
        # Normally, this requires a real TTY device, but people instantiate
        # this class often during unit tests as well. For convenience, we print
        # an error message, use standard dimensions, and go on.
        try:
            fd = stdout.fileno()
        except io.UnsupportedOperation:
            fd = None

        if not stdout.isatty() and (fd is None or fd not in cls._fds_not_a_terminal):
            msg = "Warning: Output is not a terminal (fd=%r).\n"
            sys.stderr.write(msg % fd)
            sys.stderr.flush()
            if fd is not None:
                cls._fds_not_a_terminal.add(fd)

        def get_size() -> Size:
            # If terminal (incorrectly) reports its size as 0, pick a
            # reasonable default.  See
            # https://github.com/ipython/ipython/issues/10071
            rows, columns = (None, None)

            # It is possible that `stdout` is no longer a TTY device at this
            # point. In that case we get an `OSError` in the ioctl call in
            # `get_size`. See:
            # https://github.com/prompt-toolkit/python-prompt-toolkit/pull/1021
            try:
                rows, columns = _get_size(stdout.fileno())
            except OSError:
                pass
            return Size(rows or 24, columns or 80)

        return cls(
            stdout,
            get_size,
            term=term,
            enable_bell=enable_bell,
        )

    def get_size(self) -> Size:
        return self._get_size()

    def fileno(self) -> int:
        "Return file descriptor."
        return self.stdout.fileno()

    def encoding(self) -> str:
        "Return encoding used for stdout."
        return self.stdout.encoding

    def write_raw(self, data: str) -> None:
        """
        Write raw data to output.
        """
        self._buffer.append(data)

    def write(self, data: str) -> None:
        """
        Write text to output.
        (Removes vt100 escape codes. -- used for safely writing text.)
        """
        self._buffer.append(data.replace("\x1b", "?"))

    def set_title(self, title: str) -> None:
        """
        Set terminal title.
        """
        if self.term not in (
            "linux",
            "eterm-color",
        ):  # Not supported by the Linux console.
            self.write_raw(
                "\x1b]2;%s\x07" % title.replace("\x1b", "").replace("\x07", "")
            )

    def clear_title(self) -> None:
        self.set_title("")

    def erase_screen(self) -> None:
        """
        Erases the screen with the background colour and moves the cursor to
        home.
        """
        self.write_raw("\x1b[2J")

    def enter_alternate_screen(self) -> None:
        self.write_raw("\x1b[?1049h\x1b[H")

    def quit_alternate_screen(self) -> None:
        self.write_raw("\x1b[?1049l")

    def enable_mouse_support(self):
        self.write_raw("\x1b[?1000h")
        self.write_raw("\x1b[?1003h")  # ANY_EVENT_MOUSE
        self.write_raw("\x1b[?1015h")
        self.write_raw("\x1b[?1006h")

    def disable_mouse_support(self):
        self.write_raw("\x1b[?1000l")
        self.write_raw("\x1b[?1003l")  # DISABLE ANY_EVENT_MOUSE
        self.write_raw("\x1b[?1015l")
        self.write_raw("\x1b[?1006l")

    def erase_end_of_line(self) -> None:
        """
        Erases from the current cursor position to the end of the current line.
        """
        self.write_raw("\x1b[K")

    def erase_down(self) -> None:
        """
        Erases the screen from the current line down to the bottom of the
        screen.
        """
        self.write_raw("\x1b[J")

    def reset_attributes(self) -> None:
        self.write_raw("\x1b[0m")

    def disable_autowrap(self) -> None:
        self.write_raw("\x1b[?7l")

    def enable_autowrap(self) -> None:
        self.write_raw("\x1b[?7h")

    def enable_bracketed_paste(self) -> None:
        self.write_raw("\x1b[?2004h")

    def disable_bracketed_paste(self) -> None:
        self.write_raw("\x1b[?2004l")

    def reset_cursor_key_mode(self) -> None:
        """
        For vt100 only.
        Put the terminal in cursor mode (instead of application mode).
        """
        # Put the terminal in cursor mode. (Instead of application mode.)
        self.write_raw("\x1b[?1l")

    def cursor_goto(self, row: int = 0, column: int = 0) -> None:
        """
        Move cursor position.
        """
        self.write_raw("\x1b[%i;%iH" % (row, column))

    def cursor_up(self, amount: int) -> None:
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\x1b[A")
        else:
            self.write_raw("\x1b[%iA" % amount)

    def cursor_down(self, amount: int) -> None:
        if amount == 0:
            pass
        elif amount == 1:
            # Note: Not the same as '\n', '\n' can cause the window content to
            #       scroll.
            self.write_raw("\x1b[B")
        else:
            self.write_raw("\x1b[%iB" % amount)

    def cursor_forward(self, amount: int) -> None:
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\x1b[C")
        else:
            self.write_raw("\x1b[%iC" % amount)

    def cursor_backward(self, amount: int) -> None:
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\b")  # '\x1b[D'
        else:
            self.write_raw("\x1b[%iD" % amount)

    def hide_cursor(self) -> None:
        self.write_raw("\x1b[?25l")

    def show_cursor(self) -> None:
        self.write_raw("\x1b[?12l\x1b[?25h")  # Stop blinking cursor and show.

    def flush(self) -> None:
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            return

        data = "".join(self._buffer)
        self._buffer = []

        try:
            # Ensure that `self.stdout` is made blocking when writing into it.
            # Otherwise, when uvloop is activated (which makes stdout
            # non-blocking), and we write big amounts of text, then we get a
            # `BlockingIOError` here.
            with blocking_io(self.stdout):
                # (We try to encode ourself, because that way we can replace
                # characters that don't exist in the character set, avoiding
                # UnicodeEncodeError crashes. E.g. u'\xb7' does not appear in 'ascii'.)
                # My Arch Linux installation of july 2015 reported 'ANSI_X3.4-1968'
                # for sys.stdout.encoding in xterm.
                out: IO[bytes]
                if self.write_binary:
                    if hasattr(self.stdout, "buffer"):
                        out = self.stdout.buffer
                    else:
                        # IO[bytes] was given to begin with.
                        # (Used in the unit tests, for instance.)
                        out = cast(IO[bytes], self.stdout)
                    out.write(data.encode(self.stdout.encoding or "utf-8", "replace"))
                else:
                    self.stdout.write(data)

                self.stdout.flush()
        except IOError as e:
            if e.args and e.args[0] == errno.EINTR:
                # Interrupted system call. Can happen in case of a window
                # resize signal. (Just ignore. The resize handler will render
                # again anyway.)
                pass
            elif e.args and e.args[0] == 0:
                # This can happen when there is a lot of output and the user
                # sends a KeyboardInterrupt by pressing Control-C. E.g. in
                # a Python REPL when we execute "while True: print('test')".
                # (The `ptpython` REPL uses this `Output` class instead of
                # `stdout` directly -- in order to be network transparent.)
                # So, just ignore.
                pass
            else:
                raise

    def ask_for_cpr(self) -> None:
        """
        Asks for a cursor position report (CPR).
        """
        self.write_raw("\x1b[6n")
        self.flush()

    @property
    def responds_to_cpr(self) -> bool:
        # When the input is a tty, we assume that CPR is supported.
        # It's not when the input is piped from Pexpect.
        if os.environ.get("PROMPT_TOOLKIT_NO_CPR", "") == "1":
            return False

        if is_dumb_terminal(self.term):
            return False
        try:
            return self.stdout.isatty()
        except ValueError:
            return False  # ValueError: I/O operation on closed file

    def bell(self) -> None:
        "Sound bell."
        if self.enable_bell:
            self.write_raw("\a")
            self.flush()


@contextmanager
def blocking_io(io: IO[str]) -> Iterator[None]:
    """
    Ensure that the FD for `io` is set to blocking in here.
    """
    if sys.platform == "win32":
        # On Windows, the `os` module doesn't have a `get/set_blocking`
        # function.
        yield
        return

    try:
        fd = io.fileno()
        blocking = os.get_blocking(fd)
    except:  # noqa
        # Failed somewhere.
        # `get_blocking` can raise `OSError`.
        # The io object can raise `AttributeError` when no `fileno()` method is
        # present if we're not a real file object.
        blocking = True  # Assume we're good, and don't do anything.

    try:
        # Make blocking if we weren't blocking yet.
        if not blocking:
            os.set_blocking(fd, True)

        yield

    finally:
        # Restore original blocking mode.
        if not blocking:
            os.set_blocking(fd, blocking)
