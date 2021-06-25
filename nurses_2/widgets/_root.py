import numpy as np

from .widget import DEFAULT_ATTR, Widget


class _Root(Widget):
    """
    Root widget. Meant to be instantiated by the `App` class. Renders to terminal.
    """
    def __init__(self, env_out):
        self.children = [ ]

        self.env_out = env_out
        self.resize(env_out.get_size())

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.canvas = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, DEFAULT_ATTR, dtype=object)
        self._last_canvas = self.canvas.copy()
        self._last_attrs = self.attrs.copy()

        self.erase_screen()

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
        attrs[:] = DEFAULT_ATTR

        # Paint canvas.
        super().render()

        env_out = self.env_out
        _, width = env_out.get_size()

        # Avoiding attribute lookups.
        goto = env_out.cursor_goto
        set_attr = env_out.set_attr_raw
        write_raw = env_out.write_raw
        reset = env_out.reset_attributes

        forward = env_out.cursor_forward
        up = env_out.cursor_up
        backward = env_out.cursor_backward

        def move_cursor(new_y, new_x):
            if new_y > last_y:
                write("\r\n" * (new_y - last_y))
                forward(new_x)
            elif new_y < last_y:
                up(last_y - new_y)

            if last_x >= width - 1:
                write("\r")
                forward(new_x)
            elif new_x < last_x:
                backward(last_x - new_x)
            elif new_x > last_x:
                forward(new_x - last_x)

        last_y, last_x = 0, 0
        # Only write the difs.
        for y, x in np.argwhere((last_canvas != canvas) | (last_attrs != attrs)):
            move_cursor(y, x)
            set_attr(attrs[y, x])
            write_raw(canvas[y, x])
            reset()
            last_y, last_x = y, x

        env_out.flush()

    def erase_screen(self):
        """
        Erase screen.
        """
        env_out = self.env_out

        env_out.reset_attributes()
        env_out.erase_screen()
        env_out.hide_cursor()
        env_out.flush()


