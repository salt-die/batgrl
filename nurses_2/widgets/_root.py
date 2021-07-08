import numpy as np

from .widget import Widget, overlapping_region


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(self, app, env_out, default_char, default_color):
        self._app = app
        self.env_out = env_out
        self.default_char = default_char
        self.default_color = default_color
        self.children = [ ]

        self.resize(env_out.get_size())

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.env_out.erase_screen()
        self.env_out.flush()

        self._last_canvas = np.full(dim, self.default_char, dtype=object)
        self._last_colors = np.full((*dim, 6), self.default_color, dtype=np.uint8)

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
        colors[:, :] = self.default_color

        overlap = overlapping_region
        rect = self.rect

        for child in self.children:
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
        colors = colors[ys, xs]
        chars = canvas[ys, xs]
        for y, x, color, char in zip(ys, xs, colors, chars):
            # The escape codes for moving the cursor and setting the color concatenated:
            write("\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m{}".format(y + 1, x + 1, *color, char))

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
