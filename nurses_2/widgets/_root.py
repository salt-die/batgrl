"""
Root widget.
"""
import numpy as np

from ..colors import ColorPair
from ..data_structures import *
from .widget import Widget


class _Root(Widget):
    """
    Root widget.

    Instantiated only by :class:`nurses_2.app.App`.
    """
    def __init__(
        self,
        app: "App",
        env_out: "Vt100_Output",
        background_char: str,
        background_color_pair: ColorPair,
    ):
        self._app = app
        self.children = [ ]
        self.env_out = env_out
        self.background_char = background_char
        self.background_color_pair = background_color_pair

        self.size = env_out.get_size()

    def on_size(self):
        """
        Erase last render and re-make buffers.
        """
        h, w = self._size

        self.env_out.erase_screen()
        self.env_out.flush()

        self._last_canvas = np.full((h, w), self.background_char, dtype=object)
        self._last_colors = np.full((h, w, 6), self.background_color_pair, dtype=np.uint8)

        self.canvas = self._last_canvas.copy()
        self.colors = self._last_colors.copy()

        self._redraw_all = True

        # Buffer arrays to re-use in the `render` method:
        self._char_diffs = np.zeros_like(self.canvas, dtype=bool)
        self._color_diffs = np.zeros_like(self.colors, dtype=bool)
        self._reduced_color_diffs = np.zeros_like(self.canvas, dtype=bool)

    @property
    def pos(self):
        return Point(0, 0)

    @property
    def absolute_pos(self):
        return Point(0, 0)

    @property
    def is_transparent(self):
        return False

    @property
    def is_visible(self):
        return True

    @property
    def is_enabled(self):
        return True

    @property
    def parent(self):
        return None

    @property
    def root(self):
        return self

    @property
    def app(self):
        return self._app

    def to_local(self, point: Point) -> Point:
        return point

    def collides_point(self, point: Point) -> bool:
        return True

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        # Swap canvas with last render:
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.colors, self._last_colors = self._last_colors, self.colors

        canvas = self.canvas
        colors = self.colors

        # Erase canvas:
        canvas[:] = self.background_char
        colors[:, :] = self.background_color_pair

        height, width = canvas.shape

        self.render_children((slice(0, height), slice(0, width)), canvas, colors)

        if self._redraw_all:
            ys, xs = np.indices((height, width)).reshape(2, height * width)
            self._redraw_all = False
        else:
            char_diffs = self._char_diffs
            color_diffs = self._color_diffs
            reduced_color_diffs = self._reduced_color_diffs

            # Find differences between current render and last render:
            # (`(last_canvas != canvas) | np.any(last_colors != colors, axis=-1)` with buffers.)
            np.not_equal(self._last_canvas, canvas, out=char_diffs)
            np.not_equal(self._last_colors, colors, out=color_diffs)
            np.any(color_diffs, axis=-1, out=reduced_color_diffs)
            np.logical_or(char_diffs, reduced_color_diffs, out=char_diffs)

            ys, xs = char_diffs.nonzero()

        env_out = self.env_out
        write = env_out._buffer.append

        write("\x1b7")  # Save cursor
        for y, x, (fr, fg, fb, br, bg, bb), char in zip(ys, xs, colors[ys, xs], canvas[ys, xs]):
            write(
                f"\x1b[{y + 1};{x + 1}H"  # Move cursor to (y, x)
                f"\x1b[0;38;2;{fr};{fg};{fb};48;2;{br};{bg};{bb}m"  # Set color pair
                f"{char}"  # A single unicode grapheme with optional pre- and post-pended style ansi escapes.
            )
        write("\x1b8")  # Restore cursor
        env_out.flush()
