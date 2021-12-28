from ...data_structures import Point, Size
from ...io import MouseEvent, KeyPressEvent, PasteEvent
from .._widget_base import _WidgetBase


class _FieldBase(_WidgetBase):
    """
    A widget that specializes in rendering 1x1 particles.
    """
    def resize(self, size: Size):
        self._size = size

        for child in self.children:
            child.update_geometry()

    def add_widget(self, widget):
        if not isinstance(widget, self._child_type):
            raise TypeError(
                f"expected {self._child_type.__name__}, got {type(widget).__name__}"
            )

        super().add_widget(widget)

    def add_particle(self, particle):
        """
        Alias for `add_widget`.
        """
        self.add_widget(particle)

    def walk(self):
        """
        Yield all descendents.
        """
        yield from self.children

    def dispatch_press(self, key_press_event: KeyPressEvent):
        """
        Dispatch key press to children.
        """
        # Note this dispatching is in reverse order from widget base.
        return (
            self.on_press(key_press_event)
            or any(
                particle.on_press(key_press_event)
                for particle in reversed(self.children)
                if particle.is_enabled
            )
        )

    def dispatch_click(self, mouse_event: MouseEvent):
        """
        Dispatch mouse event to children.
        """
        # Note this dispatching is in reverse order from widget base.
        return (
            self.on_click(mouse_event)
            or any(
                particle.on_click(mouse_event)
                for particle in reversed(self.children)
                if particle.is_enabled
            )
        )

    def dispatch_paste(self, paste_event: PasteEvent):
        # Note this dispatching is in reverse order from widget base.
        return (
            self.on_paste(mouse_event)
            or any(
                particle.on_paste(mouse_event)
                for particle in reversed(self.children)
                if particle.is_enabled
            )
        )


class _ParticleBase:
    """
    Base for 1x1 text or graphic elements.
    """
    def __init__(
        self,
        *,
        pos=Point(0, 0),
        is_transparent=False,
        is_visible=True,
        is_enabled=True,
    ):
        self.parent = None

        self.top, self.left = pos

        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

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

    def to_local(self, coords):
        """
        Convert absolute coordinates to relative coordinates.
        """
        y, x = self.parent.to_local(coords)
        return y - self.top, x - self.left

    def on_press(self, key_press_event: KeyPressEvent):
        """
        Handle key press event. (Handled key presses should return True else False or None).
        """

    def on_click(self, mouse_event: MouseEvent):
        """
        Handle mouse event. (Handled mouse events should return True else False or None).
        """


_FieldBase._child_type = _ParticleBase
