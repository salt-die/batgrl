"""Output for vt100 terminals."""
import json
import os
import shutil
import sys
import time
from pathlib import Path
from sys import stdout

import numpy as np

from ...gadgets._root import _Root
from ...gadgets.text_tools import char_width
from ...geometry import Size

MAX_MEM_USAGE = 5_000_000


class Vt100_Output:
    """Vt100 output."""

    def __init__(self, asciicast_path: Path | None = None):
        self.term = os.environ.get("TERM", "")
        self._buffer = []

        self.asciicast_path = asciicast_path

        if asciicast_path is not None:
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

        self._asciicast_buffer = []
        self._initial_time = time.monotonic()
        self._mem_usage = 0

    def _create_asciicast_frame(self, data):
        frame = [time.monotonic() - self._initial_time, "o", data.decode("utf-8")]
        self._asciicast_buffer.append(json.dumps(frame) + "\n")
        self._mem_usage += sys.getsizeof(self._asciicast_buffer[-1])

        if self._mem_usage > MAX_MEM_USAGE:
            self._write_asciicast_buffer()

    def _write_asciicast_buffer(self):
        """Append frames in asciicast buffer to file."""
        with self.asciicast_path.open("a") as f:
            f.writelines(self._asciicast_buffer)

        self._asciicast_buffer.clear()
        self._mem_usage = 0

    def get_size(self) -> Size:
        """Get terminal size."""
        cols, rows = shutil.get_terminal_size()
        return Size(rows, cols)

    def set_title(self, title):
        """Set terminal title."""
        if self.term not in ("linux", "eterm-color"):
            title = "".join(c for c in title if c not in "\x1b\x07")
            self._buffer.append(f"\x1b]2;{title}\x07")

    def enter_alternate_screen(self):
        """Enter alternate screen buffer."""
        self._buffer.append("\x1b[?1049h\x1b[H")

    def quit_alternate_screen(self):
        """Exit alternate screen buffer."""
        self._buffer.append("\x1b[?1049l")

    def enable_mouse_support(self):
        """Enable mouse support in terminal."""
        self._buffer.append("\x1b[?1000h" "\x1b[?1003h" "\x1b[?1015h" "\x1b[?1006h")

    def disable_mouse_support(self):
        """Disable mouse support in terminal."""
        self._buffer.append("\x1b[?1000l" "\x1b[?1003l" "\x1b[?1015l" "\x1b[?1006l")

    def reset_attributes(self):
        """Reset character attributes."""
        self._buffer.append("\x1b[0m")

    def enable_bracketed_paste(self):
        """Enable bracketed paste in terminal."""
        self._buffer.append("\x1b[?2004h")

    def disable_bracketed_paste(self):
        """Disable bracketed paste in terminal."""
        self._buffer.append("\x1b[?2004l")

    def hide_cursor(self):
        """Hide cursor in terminal."""
        self._buffer.append("\x1b[?25l")

    def show_cursor(self):
        """Show cursor in terminal."""
        self._buffer.append("\x1b[?25h")

    def flush(self):
        """Write to output stream and flush. If recording, output is saved."""
        if not self._buffer:
            return

        data = "".join(self._buffer).encode(errors="replace")
        self._buffer.clear()

        if self.asciicast_path is not None:
            self._create_asciicast_frame(data)

        stdout.buffer.write(data)
        stdout.flush()

    def restore_console(self):
        """Restore console and finalize asciicast if recording."""
        if self.asciicast_path:
            self._write_asciicast_buffer()

    def __enter__(self):
        self.enable_mouse_support()
        self.enable_bracketed_paste()
        self.enter_alternate_screen()
        self.hide_cursor()
        self.flush()

    def __exit__(self, exc_type, exc_value, traceback):
        self.quit_alternate_screen()
        self.reset_attributes()
        self.disable_mouse_support()
        self.disable_bracketed_paste()
        self.show_cursor()
        self.flush()
        self.restore_console()

    def render_frame(self, root: _Root):
        """Render a frame of the running app."""
        canvas = root.canvas
        h, w = root.size
        if root._resized:
            root._resized = False
            ys, xs = np.indices((h, w)).reshape(2, h * w)
        else:
            diffs = root._last_canvas != canvas
            ys, xs = diffs.nonzero()

        write = self._buffer.append

        write("\x1b7")  # Save cursor
        for y, x, cell in zip(ys, xs, canvas[ys, xs]):
            (
                char,
                bold,
                italic,
                underline,
                strikethrough,
                overline,
                (fr, fg, fb),  # foreground color
                (br, bg, bb),  # background color
            ) = cell.item()

            # The following conditions ensure full-width glyphs "have enough room" else
            # they are not painted.
            if char == "":
                # `""` is used to indicate the character before it is a full-width
                # character. If this char is appearing in the diffs, we probably need to
                # repaint the full-width character before it, but if the character
                # before it isn't full-width paint whitespace instead.
                if x > 0 and char_width(canvas["char"][y, x - 1].item()) == 2:
                    x -= 1
                    (
                        char,
                        bold,
                        italic,
                        underline,
                        strikethrough,
                        overline,
                        (fr, fg, fb),
                        (br, bg, bb),
                    ) = canvas[y, x].item()
                else:
                    char = " "
            elif (
                x + 1 < w
                and canvas["char"][y, x + 1].item() != ""
                and char_width(char) == 2
            ):
                # If the character is full-width, but the following character isn't
                # `""`, assume the full-width character is being clipped, and paint
                # whitespace instead.
                char = " "

            write(
                f"\x1b[{y + 1};{x + 1}H"  # Move cursor to (y, x)
                "\x1b[0;"  # Reset
                f"{'1;' if bold else ''}"
                f"{'3;' if italic else ''}"
                f"{'4;' if underline else ''}"
                f"{'9;' if strikethrough else ''}"
                f"{'53;' if overline else ''}"
                f"38;2;{fr};{fg};{fb};48;2;{br};{bg};{bb}m"  # Set color pair
                f"{char}"
            )
        write("\x1b8")  # Restore cursor
        self.flush()
