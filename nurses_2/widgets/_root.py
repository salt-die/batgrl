import numpy as np

from .widget import Widget
from ..colors import WHITE_ON_BLACK


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(self, env_out, *, default_color=WHITE_ON_BLACK):
        self.env_out = env_out
        self.default_color = default_color
        self.children = [ ]

        self.resize(env_out.get_size())

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.env_out.erase_screen()

        self._last_canvas = np.full(dim, " ", dtype=object)
        self._last_attrs = np.zeros((*dim, 6), dtype=np.uint8)
        self._last_attrs[:, :] = self.default_color

        self.canvas = np.full_like(self._last_canvas, "><")  # `><` will guarantee an entire screen redraw.
        self.attrs = self._last_attrs.copy()

        for child in self.children:
            child.update_geometry(dim)

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

    def render(self):
        """
        Paint canvas. Render to terminal.
        """
        # Swap canvas with last render.
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.attrs, self._last_attrs = self._last_attrs, self.attrs

        canvas = self.canvas
        attrs = self.attrs

        last_canvas = self._last_canvas
        last_attrs = self._last_attrs

        # Erase canvas.
        canvas[:] = " "
        attrs[:, :] = self.default_color

        # Paint canvas.
        super().render()

        env_out = self.env_out

        # Avoiding attribute lookups.
        write = env_out._buffer.append

        # Only write the difs.
        for y, x in np.argwhere((last_canvas != canvas) | np.all(last_attrs != attrs, axis=-1)):
            write("\x1b[?25l\x1b[{};{}H\x1b[0;38;2;{};{};{};48;2;{};{};{}m{}".format(y, x, *attrs[y, x], canvas[y, x]))

        write("\x1b[0m")
        env_out.flush()
