import numpy as np

from ...colors import BLACK
from .graphic_widget import GraphicWidget


class GraphicParticleField(GraphicWidget):
    """
    A widget that only has `GraphicParticle` children.

    Notes
    -----
    ParticleFields are an optimized way to render many .5x1 TUI elements.

    Raises
    ------
    TypeError if `add_widget` argument is not an instance of `GraphicParticle`.
    """
    def __init__(self, dim=(10, 10), pos=(0, 0), *, is_visible=True):
        self._dim = dim
        self.top, self.left = pos
        self.is_visible = is_visible

        self.parent = None
        self.children = [ ]

        self.buffer = np.zeros((3, ), dtype=np.float16)

    def resize(self, dim):
        """
        Resize widget.
        """
        self._dim = dim

        for child in self.children:
            child.update_geometry()

    def add_widget(self, widget):
        if not isinstance(widget, GraphicParticle):
            raise TypeError(f"expected GraphicParticle, got {type(widget).__name__}")

        super().add_widget(widget)

    def walk(self):
        yield self
        yield from self.children

    def render(self, colors_view, rect):
        """
        Paint region given by rect into colors_view.
        """
        buffer = self.buffer
        subtract, multiply, add = np.subtract, np.multiply, np.add
        t, l, _, _, h, w = rect

        for child in self.children:
            ct = child.top
            top, left = int(ct) - t, child.left - l

            if 0 <= top < h and 0 <= left < w:
                color = colors_view[top, left, int((ct % 1) >= .5)]
                subtract(child.color, color, out=buffer, dtype=np.float16)
                multiply(buffer, child.alpha, out=buffer)
                add(buffer, color, out=color, casting="unsafe")

    def dispatch_press(self, key_press):
        """
        Try to handle key press; if not handled, dispatch event to particles until handled.
        """
        return (
            self.on_press(key_press)
            or any(particle.on_press(key_press) for particle in reversed(self.children))
        )

    def dispatch_click(self, mouse_event):
        return (
            self.on_click(mouse_event)
            or any(particle.on_click(mouse_event) for particle in reversed(self.children))
        )


class GraphicParticle:
    """
    A .5x1 TUI element that's Widget-like, except it has no render method.

    Requires a `GraphicParticleField` to be rendered.

    Notes
    -----
    The y-component of `pos` can be a float. The fractional part determines
    whether the half block is upper or lower.
    """
    def __init__(self, pos=(0, 0), *, color=BLACK, alpha=1.0):
        self.top, self.left = pos
        self.color = color
        self.alpha = alpha
        self.parent = None

    def update_geometry(self):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def dim(self):
        return 1, 1

    @property
    def pos(self):
        return self.top, self.left

    @property
    def height(self):
        return 1

    @property
    def width(self):
        return 1

    @property
    def bottom(self):
        return self.top + 1

    @property
    def right(self):
        return self.left + 1

    def absolute_to_relative_coords(self, coords):
        """
        Convert absolute coordinates to relative coordinates.
        """
        y, x = self.parent.absolute_to_relative_coords(coords)
        return y - self.top, x - self.left

    def on_press(self, key_press):
        """
        Handle key press. (Handled key presses should return True else False or None).

        Notes
        -----
        `key_press` is a `prompt_toolkit` `KeyPress`.
        """

    def on_click(self, mouse_event):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).

        Notes
        -----
        `mouse_event` is a `prompt_toolkit` MouseEvent`.
        """
