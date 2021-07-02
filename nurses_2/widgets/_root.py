import numpy as np

from .widget import Widget
from ..colors import WHITE_ON_BLACK


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(self, env_out):
        self.env_out = env_out
        self.default_color = WHITE_ON_BLACK
        self.children = [ ]

        self.resize(env_out.get_size())

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.env_out.erase_screen()

        self._last_canvas = np.full(dim, " ", dtype=object)
        self._last_colors = np.zeros((*dim, 6), dtype=np.uint8)
        self._last_colors[:, :] = self.default_color

        self.canvas = np.full_like(self._last_canvas, "><")  # "><" will guarantee an entire screen redraw.
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
    def is_transparent(self):
        return False

    @property
    def is_visible(self):
        return True

    @property
    def parent(self):
        return None

    @property
    def root(self):
        return self

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

        last_canvas = self._last_canvas
        last_colors = self._last_colors

        char_diffs = self._char_diffs
        color_diffs = self._color_diffs
        reduced_color_diffs = self._reduced_color_diffs

        env_out = self.env_out
        write = env_out._buffer.append

        # Erase canvas:
        canvas[:] = " "
        colors[:, :] = self.default_color

        super().render()  # Paint canvas

        # Find differences between current render and last render:
        # (This is optimized version of `(last_canvas != canvas) | np.any(last_colors != colors, axis=-1)`
        # that re-uses buffers instead of creating new arrays.)
        np.not_equal(last_canvas, canvas, out=char_diffs)
        np.not_equal(last_colors, colors, out=color_diffs)
        np.any(color_diffs, axis=-1, out=reduced_color_diffs)
        np.logical_or(char_diffs, reduced_color_diffs, out=char_diffs)

        write("\x1b[?25l")  # Hide cursor

        for y, x in np.argwhere(char_diffs):
            # The escape codes for moving the cursor and setting the color concatenated:
            write("\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m{}".format(y + 1, x + 1, *colors[y, x], canvas[y, x]))

        write("\x1b[0m")  # Reset attributes
        env_out.flush()

    def dispatch_press(self, key_press):
        """
        Dispatch key press to descendants until handled.
        """
        return any(widget.dispatch_press(key_press) for widget in reversed(self.children))

    def dispatch_click(self, mouse_event):
        """
        Dispatch mouse event to descendents until handled.
        """
        return any(widget.dispatch_click(mouse_event) for widget in reversed(self.children))
