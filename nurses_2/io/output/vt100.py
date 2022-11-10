"""
Output for vt100 terminals.
"""
import json
import os
import time
import sys
from pathlib import Path
from sys import stdout

from ...data_structures import Size

MAX_MEM_USAGE = 5_000_000


class Vt100_Output:
    def __init__(self, asciicast_path: Path | None):
        self.term = os.environ.get("TERM", "")
        self._buffer = [ ]

        self.asciicast_path = asciicast_path

        if asciicast_path:
            self._init_asciicast()

    def _init_asciicast(self):
        size = self.get_size()

        metadata = {
            "version": 2,
            "width": size.width,
            "height": size.height,
            "timestamp": int(time.time()),
            "env": {
                "TERM": self.term,
                "SHELL": os.environ.get("SHELL", ""),
            },
        }

        self.asciicast_path.write_text(json.dumps(metadata) + "\n")

        self._asciicast_buffer = [ ]
        self._initial_time = time.monotonic()
        self._mem_usage = 0

    def _create_asciicast_frame(self, data):
        frame = [time.monotonic() - self._initial_time, "o", data.decode("utf-8")]
        self._asciicast_buffer.append(json.dumps(frame) + "\n")
        self._mem_usage += sys.getsizeof(self._asciicast_buffer[-1])

        if self._mem_usage > MAX_MEM_USAGE:
            self._write_asciicast_buffer()

    def _write_asciicast_buffer(self):
        """
        Append frames in asciicast buffer to file.
        """
        with self.asciicast_path.open("a") as f:
            f.writelines(self._asciicast_buffer)

        self._asciicast_buffer.clear()
        self._mem_usage = 0

    def get_size(self) -> Size:
        cols, rows = os.get_terminal_size()
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
        Erase the screen and move cursor to home.
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

    def hide_cursor(self):
        self._buffer.append("\x1b[?25l")

    def show_cursor(self):
        self._buffer.append("\x1b[?25h")

    def flush(self):
        """
        Write to output stream and flush. If recording, output is saved.
        """
        if not self._buffer:
            return

        data = "".join(self._buffer).encode(errors="replace")
        self._buffer.clear()

        if self.asciicast_path is not None:
            self._create_asciicast_frame(data)

        stdout.buffer.write(data)
        stdout.flush()

    def restore_console(self):
        """
        Restore console and finalize asciicast if recording.
        """
        if self.asciicast_path:
            self._write_asciicast_buffer()
