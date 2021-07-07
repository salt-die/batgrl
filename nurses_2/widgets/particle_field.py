from .widget import Widget
from ..colors import WHITE_ON_BLACK


class ParticleField(Widget):
    """
    A widget that only has `Particle` children.

    Notes
    -----
    ParticleFields are an optimized way to render many 1x1 TUI elements.

    Raises
    ------
    TypeError if `add_widget` argument is not an instance of `Particle`.
    """
    def __init__(self, dim=(10, 10), pos=(0, 0), *, is_visible=True, **kwargs):
        self._height, self._width = dim
        self.top, self.left = pos
        self.is_visible = is_visible

        self.parent = None
        self.children = [ ]

    def resize(self, dim):
        self._height, self._width = dim

        for child in self.children:
            child.update_geometry()

    @property
    def dim(self):
        return self.height, self.width

    @property
    def height(self):
        return self._height

    @property
    def width(self):
        return self._width

    def add_text(self, text, row=0, column=0):
        raise NotImplemented

    @property
    def get_view(self):
        raise NotImplemented

    def add_widget(self, widget):
        if not isinstance(widget, Particle):
            raise TypeError(f"expected Particle, got {type(widget).__name__}")

        super().add_widget(widget)

    def walk(self):
        yield self
        yield from self.children

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, _, _, h, w = rect

        for child in self.children:
            pos = top, left = child.top - t, child.left - l

            if (
                child.is_visible
                and not (child.is_transparent and child.char == " ")
                and 0 <= top < h
                and 0 <= left < w
            ):
                canvas_view[pos] = child.char
                colors_view[pos] = child.color

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


class Particle:
    """
    A 1x1 TUI element that's Widget-like, except it has no render method.
    Particles require a `ParticleField` parent to be rendered.
    """
    def __init__(
        self,
        pos=(0, 0),
        *,
        char=" ",
        color=WHITE_ON_BLACK,
        is_transparent=False,
        is_visible=True,
    ):
        self.char = char
        self.color = color

        self.top, self.left = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible
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

    @property
    def middle(self):
        return 0, 0

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
