"""
Grabbable behavior for a widget.
"""
from ...data_structures import Point
from ...io import MouseEventType, MouseButton


class GrabbableBehavior:
    """
    Grabbable behavior for a widget. Mouse down events that collide with widget will "grab"
    it, calling :meth:`grab`. While grabbed, each mouse event will call :meth:`grab_update`
    until the widget is ungrabbed, i.e., a mouse up event is received (which calls
    :meth:`ungrab`).

    To customize grabbable behavior, implement any of :meth:`grab`, :meth:`grab_update`,
    or :meth:`ungrab`.

    For convenience, the change in mouse position is available through :attr:`mouse_dyx`,
    :attr:`mouse_dy`, and :attr:`mouse_dx`.

    Parameters
    ----------
    is_grabbable : bool, default: True
        If False, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.

    Attributes
    ----------
    is_grabbable : bool, default: True
        If False, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
    is_grabbed : bool
        True if widget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.

    Methods
    -------
    grab:
        Grab the widget.
    ungrab:
        Ungrab the widget.
    grab_update:
        Update widget with incoming mouse events while grabbed.
    """
    def __init__(
        self,
        *,
        is_grabbable: bool=True,
        disable_ptf: bool=False,
        mouse_button: MouseButton=MouseButton.LEFT,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.is_grabbable = is_grabbable
        self.disable_ptf = disable_ptf
        self.mouse_button = mouse_button
        self._is_grabbed = False

        self._last_mouse_pos = Point(0, 0)
        self._mouse_dyx = Point(0, 0)

    def on_mouse(self, mouse_event):
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
        return self._is_grabbed

    @property
    def mouse_dyx(self) -> Point:
        """
        Last change in mouse position.
        """
        return self._mouse_dyx

    @property
    def mouse_dy(self) -> int:
        """
        Vertical change in mouse position.
        """
        return self._mouse_dyx[0]

    @property
    def mouse_dx(self) -> int:
        """
        Horizontal change in mouse position.
        """
        return self._mouse_dyx[1]

    def grab(self, mouse_event):
        """
        Grab widget.
        """
        self._is_grabbed = True

        if not self.disable_ptf:
            self.pull_to_front()

    def ungrab(self, mouse_event):
        """
        Ungrab widget.
        """
        self._is_grabbed = False

    def grab_update(self, mouse_event):
        """
        Update grabbed widget with incoming mouse event.
        """
