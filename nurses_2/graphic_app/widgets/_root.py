import numpy as np

from .graphic_widget import GraphicWidget, overlapping_region


class _GraphicRoot(GraphicWidget):
    """
    Root widget of a graphic app.
    """
    def __init__(self, app, env_out, default_color):
        self._app = app
        self.env_out = env_out
        self.default_color = default_color
        self.children = [ ]

        self.resize(env_out.get_size())

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

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.env_out.erase_screen()
        self.env_out.flush()

        self._dim = h, w = dim
        self._last_colors = np.full((h, w, 2, 3),  self.default_color, dtype=np.uint8)

        self.colors = self._last_colors.copy()

        # Buffer arrays to re-use in the `render` method:
        self._color_diffs = np.zeros_like(self.colors, dtype=np.bool8)
        self._reduced_color_diffs = np.zeros((h, w), dtype=np.bool8)

        for child in self.children:
            child.update_geometry()

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        # Swap canvas with last render:
        self.colors, self._last_colors = self._last_colors, self.colors

        # Bring arrays into locals:
        colors = self.colors

        color_diffs = self._color_diffs
        reduced_color_diffs = self._reduced_color_diffs

        env_out = self.env_out
        write = env_out._buffer.append

        # Erase canvas:
        colors[:] = self.default_color

        overlap = overlapping_region
        rect = self.rect

        for child in self.children:
            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(colors[dest_slice], child_rect)

        np.not_equal(self._last_colors, colors, out=color_diffs)
        np.any(color_diffs, axis=(2, 3), out=reduced_color_diffs)

        write("\x1b[?25l")  # Hide cursor

        ys, xs = np.nonzero(reduced_color_diffs)
        for y, x, (fore, back) in zip(ys, xs, colors[ys, xs]):
            # The escape codes for moving the cursor and setting the color concatenated:
            write("\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m▀".format(y + 1, x + 1, *fore, *back))

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
