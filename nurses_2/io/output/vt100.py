"""
Output for vt100 terminals.
"""
import errno
import os
import sys

from ...data_structures import Size
from ..utils import get_term_environment_variable


class Vt100_Output:
    def __init__(self):
        self.stdout = sys.stdout
        self.term = get_term_environment_variable()

        self._buffer = [ ]

    def get_size(self) -> Size:
        size = os.get_terminal_size(self.stdout.fileno())
        return Size(size.lines, size.columns)

    def fileno(self):
        """
        Stdout file descriptor.
        """
        return self.stdout.fileno()

    def encoding(self):
        """
        Stdout encoding.
        """
        return self.stdout.encoding

    def write_raw(self, data):
        """
        Write raw data to output.
        """
        self._buffer.append(data)

    def write(self, data):
        """
        Write text to output.
        (Removes vt100 escape codes. -- used for safely writing text.)
        """
        self._buffer.append(data.replace("\x1b", "?"))

    def set_title(self, title):
        """
        Set terminal title.
        """
        if self.term not in ("linux", "eterm-color"):
            title = title.replace("\x1b", "").replace("\x07", "")
            self.write_raw(
                f'\x1b]2;{title}\x07'
            )

    def clear_title(self):
        self.set_title("")

    def erase_screen(self):
        """
        Erases the screen with the background colour and moves the cursor to
        home.
        """
        self.write_raw("\x1b[2J")

    def enter_alternate_screen(self):
        self.write_raw("\x1b[?1049h\x1b[H")

    def quit_alternate_screen(self):
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

    def erase_end_of_line(self):
        """
        Erases from the current cursor position to the end of the current line.
        """
        self.write_raw("\x1b[K")

    def erase_down(self):
        """
        Erases the screen from the current line down to the bottom of the
        screen.
        """
        self.write_raw("\x1b[J")

    def reset_attributes(self):
        self.write_raw("\x1b[0m")

    def disable_autowrap(self):
        self.write_raw("\x1b[?7l")

    def enable_autowrap(self):
        self.write_raw("\x1b[?7h")

    def enable_bracketed_paste(self):
        self.write_raw("\x1b[?2004h")

    def disable_bracketed_paste(self):
        self.write_raw("\x1b[?2004l")

    def reset_cursor_key_mode(self):
        """
        For vt100 only.
        Put the terminal in cursor mode (instead of application mode).
        """
        # Put the terminal in cursor mode. (Instead of application mode.)
        self.write_raw("\x1b[?1l")

    def cursor_goto(self, row=0, column=0):
        """
        Move cursor position.
        """
        self.write_raw(f"\x1b[{row};{column}H")

    def cursor_up(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\x1b[A")
        else:
            self.write_raw(f"\x1b[{amount}A")

    def cursor_down(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\x1b[B")
        else:
            self.write_raw(f"\x1b[{amount}B")

    def cursor_forward(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\x1b[C")
        else:
            self.write_raw(f"\x1b[{amount}C")

    def cursor_backward(self, amount):
        if amount == 0:
            pass
        elif amount == 1:
            self.write_raw("\b")  # '\x1b[D'
        else:
            self.write_raw(f"\x1b[{amount}D")

    def hide_cursor(self):
        self.write_raw("\x1b[?25l")

    def show_cursor(self):
        self.write_raw("\x1b[?12l\x1b[?25h")  # Stop blinking cursor and show.

    def flush(self):
        """
        Write to output stream and flush.
        """
        if not self._buffer:
            return

        data = "".join(self._buffer)
        self._buffer = [ ]
        out = self.stdout

        try:
            out.buffer.write(data.encode(out.encoding or "utf-8", "replace"))
            out.flush()

        except IOError as e:
            if not (e.args and (e.args[0] == errno.EINTR or e.args[0] == 0)):
                raise

    def ask_for_cpr(self):
        """
        Asks for a cursor position report (CPR).
        """
        self.write_raw("\x1b[6n")
        self.flush()

    def bell(self):
        """
        Play bell sound.
        """
        self.write_raw("\a")
        self.flush()

    def restore_console(self):
        """
        Windows only.
        """
