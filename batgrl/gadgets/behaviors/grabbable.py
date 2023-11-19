"""Grabbable behavior for a gadget."""
from ...io import MouseButton, MouseEvent, MouseEventType
from ..gadget import Point

__all__ = ["Grabbable"]


class Grabbable:
    """
    Grabbable behavior for a gadget.

    Mouse down events that collide with the gadget will "grab" it, calling :meth:`grab`.
    While grabbed, each mouse event will call :meth:`grab_update` until the gadget is
    ungrabbed, i.e., a mouse up event is received (which calls :meth:`ungrab`).

    To customize grabbable behavior, implement any of :meth:`grab`, :meth:`grab_update`,
    or :meth:`ungrab`.

    For convenience, the change in mouse position is available through
    :attr:`mouse_dyx`, :attr:`mouse_dy`, and :attr:`mouse_dx`.

    Parameters
    ----------
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.

    Attributes
    ----------
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        True if gadget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.

    Methods
    -------
    grab(mouse_event):
        Grab the gadget.
    ungrab(mouse_event):
        Ungrab the gadget.
    grab_update(mouse_event):
        Update gadget with incoming mouse events while grabbed.
    """

    def __init__(
        self,
        *,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.is_grabbable = is_grabbable
        self.disable_ptf = disable_ptf
        self.mouse_button = mouse_button
        self._is_grabbed = False

        self._last_mouse_pos = Point(0, 0)
        self._mouse_dyx = Point(0, 0)

    def on_mouse(self, mouse_event):
        """Determine if mouse event grabs or ungrabs gadget."""
        last_y, last_x = self._last_mouse_pos
        y, x = self._last_mouse_pos = mouse_event.position
        self._mouse_dyx = Point(y - last_y, x - last_x)

        if self.is_grabbable:
            if self.is_grabbed:
                if mouse_event.event_type == MouseEventType.MOUSE_UP:
                    self.ungrab(mouse_event)
                else:
                    self.grab_update(mouse_event)

                return True

            if (
                self.collides_point(mouse_event.position)
                and mouse_event.event_type == MouseEventType.MOUSE_DOWN
                and mouse_event.button == self.mouse_button
            ):
                self.grab(mouse_event)
                return True

        return super().on_mouse(mouse_event)

    @property
    def is_grabbed(self) -> bool:
        """True if gadget is grabbed."""
        return self._is_grabbed

    @property
    def mouse_dyx(self) -> Point:
        """Last change in mouse position."""
        return self._mouse_dyx

    @property
    def mouse_dy(self) -> int:
        """Vertical change in mouse position."""
        return self._mouse_dyx[0]

    @property
    def mouse_dx(self) -> int:
        """Horizontal change in mouse position."""
        return self._mouse_dyx[1]

    def grab(self, mouse_event: MouseEvent):
        """
        Grab gadget.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that grabbed the gadget.
        """
        self._is_grabbed = True

        if not self.disable_ptf:
            self.pull_to_front()

    def ungrab(self, mouse_event: MouseEvent):
        """
        Ungrab gadget.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that ungrabbed the gadget.
        """
        self._is_grabbed = False

    def grab_update(self, mouse_event: MouseEvent):
        """
        Update grabbed gadget with incoming mouse event.

        Parameters
        ----------
        mouse_event : MouseEvent
            The mouse event that updates the grabbed gadget.
        """
