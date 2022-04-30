"""
Output for vt100 terminals.
"""
import json
import time
from errno import EINTR
from os import get_terminal_size
from pathlib import Path
from sys import stdout

from ...data_structures import Size
from ..environ import get_term_environment_variable


class Vt100_Output:
    def __init__(self, asciicast_path: Path | None):
        self.term = get_term_environment_variable()
        self._buffer = [ ]

        self.asciicast_path = asciicast_path
        if asciicast_path:
            size = self.get_size()

            self._asciicast = [
                f'{{"version": 2, "width": {size.width}, '
                f'"height": {size.height}, "timestamp": {int(time.time())}}}'
            ]  # Asciicast metadata
            # TODO: Add `TERM` and `SHELL` metadata
            # TODO: "env": {"TERM": ..., "SHELL": ...}

            self._initial_time = time.monotonic()

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

        if self.asciicast_path:
            metadata = json.loads(self._asciicast[0])
            metadata["title"] = title
            self._asciicast[0] = json.dumps(metadata)

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
        Write to output stream and flush. If recording, data is saved.
        """
        if not self._buffer:
            return

        data = "".join(self._buffer).encode(errors="replace")
        self._buffer.clear()

        if self.asciicast_path is not None:
            # TODO: Check the size of the asciicast and write to disk periodically to
            # TODO: prevent using too much memory.
            self._asciicast.append(
                json.dumps(
                    [time.monotonic() - self._initial_time, "o", data.decode("utf-8")]
                )
            )

        try:
            stdout.buffer.write(data)
            stdout.flush()
            return data

        except IOError as e:
            if not (e.args and e.args[0] in (0, EINTR)):
                raise

    def restore_console(self):
        """
        Restore console and finalize asciicast if recording.
        """
        if self.asciicast_path:
            # ?: Write in append mode?
            self.asciicast_path.write_text("\n".join(self._asciicast))
