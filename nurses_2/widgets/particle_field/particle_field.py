from ...colors import WHITE_ON_BLACK
from ...data_structures import Point, Size
from ...io import Keys, MouseEvent
from ..widget import Widget
from ..widget_data_structures import Rect


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
    def __init__(self, size=Size(10, 10), pos=Point(0, 0), *, is_visible=True, is_enabled=True):
        self._size = size
        self.top, self.left = pos
        self.is_visible = is_visible
        self.is_enabled = is_enabled

        self.parent = None
        self.children = [ ]

    def resize(self, size: Size):
        self._size = size

        for child in self.children:
            child.update_geometry()

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

    def render(self, canvas_view, colors_view, rect: Rect):
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

    def dispatch_press(self, key):
        """
        Dispatch key press to children.
        """
        # Note this dispatching is in reverse order from widget base.
        return (
            self.on_press(key)
            or any(particle.on_press(key) for particle in reversed(self.children) if particle.is_visible)
        )

    def dispatch_click(self, mouse_event):
        """
        Dispatch mouse event to children.
        """
        # Note this dispatching is in reverse order from widget base.
        return (
            self.on_click(mouse_event)
            or any(particle.on_click(mouse_event) for particle in reversed(self.children) if particle.is_visible)
        )


class Particle:
    """
    A 1x1 TUI element that's Widget-like, except it has no render method.
    Particles require a `ParticleField` parent to be rendered.
    """
    def __init__(
        self,
        pos=Point(0, 0),
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
    def size(self):
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

    def on_press(self, key: Keys):
        """
        Handle key press. (Handled key presses should return True else False or None).
        """

    def on_click(self, mouse_event: MouseEvent):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """
