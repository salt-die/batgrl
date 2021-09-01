import numpy as np

from ..colors import Color
from ..data_structures import Point, Size
from .widget import Widget, overlapping_region
from .widget_data_structures import Rect


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(self, app, env_out, default_char, default_color_pair: Color):
        self._app = app
        self.env_out = env_out
        self.default_char = default_char
        self.default_color_pair = default_color_pair
        self.children = [ ]

        self.resize(env_out.get_size())

    def resize(self, size: Size):
        """
        Resize canvas. Last render is erased.
        """
        self.env_out.erase_screen()
        self.env_out.flush()

        self._size = size

        self._last_canvas = np.full(size, self.default_char, dtype=object)
        self._last_colors = np.full((*size, 6), self.default_color_pair, dtype=np.uint8)

        invalidate_char = "a" if "a" != self.default_char else "b"  # A character that guarantees full-screen redraw.
        self.canvas = np.full_like(self._last_canvas, invalidate_char)
        self.colors = self._last_colors.copy()

        # Buffer arrays to re-use in the `render` method:
        self._char_diffs = np.zeros_like(self.canvas, dtype=np.bool8)
        self._color_diffs = np.zeros_like(self.colors, dtype=np.bool8)
        self._reduced_color_diffs = np.zeros_like(self.canvas, dtype=np.bool8)

        for child in self.children:
            child.update_geometry()

    @property
    def top(self):
        return 0

    @property
    def left(self):
        return 0

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

    def absolute_to_relative_coords(self, coord):
        return coord

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        # Swap canvas with last render:
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.colors, self._last_colors = self._last_colors, self.colors

        # Bring arrays into locals:
        canvas = self.canvas
        colors = self.colors

        char_diffs = self._char_diffs
        color_diffs = self._color_diffs
        reduced_color_diffs = self._reduced_color_diffs

        env_out = self.env_out
        write = env_out._buffer.append

        # Erase canvas:
        canvas[:] = self.default_char
        colors[:, :] = self.default_color_pair

        overlap = overlapping_region
        height, width = canvas.shape
        rect = Rect(
            0,
            0,
            height,
            width,
            height,
            width,
        )

        for child in self.children:
            if not child.is_visible or not child.is_enabled:
                continue

            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(canvas[dest_slice], colors[dest_slice], child_rect)

        # Find differences between current render and last render:
        # (This is optimized version of `(last_canvas != canvas) | np.any(last_colors != colors, axis=-1)`
        # that re-uses buffers instead of creating new arrays.)
        np.not_equal(self._last_canvas, canvas, out=char_diffs)
        np.not_equal(self._last_colors, colors, out=color_diffs)
        np.any(color_diffs, axis=-1, out=reduced_color_diffs)
        np.logical_or(char_diffs, reduced_color_diffs, out=char_diffs)

        write("\x1b[?25l")  # Hide cursor

        ys, xs = np.nonzero(char_diffs)
        for y, x, color, char in zip(ys, xs, colors[ys, xs], canvas[ys, xs]):
            # The escape codes for moving the cursor and setting the color concatenated:
            write("\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m{}".format(y + 1, x + 1, *color, char))

        write("\x1b[0m")  # Reset attributes
        env_out.flush()

    def dispatch_press(self, key):
        """
        Dispatch key press to descendants until handled.
        """
        any(widget.dispatch_press(key) for widget in reversed(self.children) if widget.is_enabled)

    def dispatch_click(self, mouse_event):
        """
        Dispatch mouse event to descendents until handled.
        """
        any(widget.dispatch_click(mouse_event) for widget in reversed(self.children) if widget.is_enabled)
