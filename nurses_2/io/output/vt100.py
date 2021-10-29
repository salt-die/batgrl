"""
Output for vt100 terminals.
"""
from errno import EINTR
from os import get_terminal_size
from sys import stdout

from ...data_structures import Size
from ..environ import get_term_environment_variable


class Vt100_Output:
    def __init__(self):
        self.term = get_term_environment_variable()
        self._buffer = [ ]

    def get_size(self) -> Size:
        cols, rows = get_terminal_size()
        return Size(rows, cols)

    def set_title(self, title):
        """
        Set terminal title.
        """
        if self.term not in ("linux", "eterm-color"):
            title = "".join(c for c in title if c not in "\x1b\x07")
            self._buffer.append(f"\x1b]2;{title}\x07")

    def clear_title(self):
        self.set_title("")

    def erase_screen(self):
        """
        Erases the screen with the background colour and moves the cursor to
        home.
        """
        self._buffer.append("\x1b[2J")

    def enter_alternate_screen(self):
        self._buffer.append("\x1b[?1049h\x1b[H")

    def quit_alternate_screen(self):
        self._buffer.append("\x1b[?1049l")

    def enable_mouse_support(self):
        self._buffer.append(
            "\x1b[?1000h"
            "\x1b[?1003h"
            "\x1b[?1015h"
            "\x1b[?1006h"
        )

    def disable_mouse_support(self):
        self._buffer.append(
            "\x1b[?1000l"
            "\x1b[?1003l"
            "\x1b[?1015l"
            "\x1b[?1006l"
        )

    def reset_attributes(self):
        self._buffer.append("\x1b[0m")

    def enable_bracketed_paste(self):
        self._buffer.append("\x1b[?2004h")

    def disable_bracketed_paste(self):
        self._buffer.append("\x1b[?2004l")

    def show_cursor(self):
        self._buffer.append("\x1b[?25h")

    def flush(self):
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            return

        data = "".join(self._buffer)
        self._buffer.clear()

        try:
            stdout.buffer.write(data.encode(errors="replace"))
            stdout.flush()

        except IOError as e:
            if not (e.args and e.args[0] in (0, EINTR)):
                raise

    def restore_console(self):
        """
        Windows only.
        """
