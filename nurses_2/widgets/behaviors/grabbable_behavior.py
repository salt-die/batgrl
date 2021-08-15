from ...mouse import MouseEventType
from ..widget_data_structures import Point


class GrabbableBehavior:
    """
    Grabbable behavior for a widget. Mouse down events that collide with widget will "grab"
    it, calling the `grab` method. While grabbed, each mouse event will call `grab_update`
    until the widget is ungrabbed, i.e., a mouse up event is received (which calls the `ungrab`
    method).

    To customize grabbable behavior, implement any of `grab`, `grab_update`, or `ungrab` methods.

    For convenience, the change in mouse position is updated while grabbed and made available
    through the `mouse_dyx`, `mouse_dy`, and `mouse_dx` properties.

    Set `is_grabbable` to False to disable this behavior.
    """
    def __init__(self, *args, is_grabbable=True, **kwargs):
        super().__init__(*args, **kwargs)

        self.is_grabbable = is_grabbable
        self._is_grabbed = False
        self._mouse_dyx = Point(0, 0)

    def on_click(self, mouse_event):
        if super().on_click(mouse_event):
            return True

        if not self.is_grabbable:
            if self._is_grabbed:
                self.ungrab(mouse_event)

            return False

        if self.is_grabbed:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.ungrab(mouse_event)
            else:
                last_y, last_x = self._last_mouse_pos
                y, x = self._last_mouse_pos = mouse_event.position
                self._mouse_dyx = Point(y - last_y, x - last_x)
                self.grab_update(mouse_event)

            return True

        if (
            self.collides_coords(mouse_event.position)
            and mouse_event.event_type == MouseEventType.MOUSE_DOWN
        ):
            self.grab(mouse_event)

            return True

    @property
    def is_grabbed(self):
        return self._is_grabbed

    @property
    def mouse_dyx(self):
        """
        Change in mouse position. Only updated while grabbed.
        """
        return self._mouse_dyx

    @property
    def mouse_dy(self):
        """
        Vertical change in mouse position. Only updated while grabbed.
        """
        return self._mouse_dyx[0]

    @property
    def mouse_dx(self):
        """
        Horizontal change in mouse position. Only updated while grabbed.
        """
        return self._mouse_dyx[1]

    def grab(self, mouse_event):
        """
        Grab widget.
        """
        self._is_grabbed = True
        self._last_mouse_pos = mouse_event.position


    def ungrab(self, mouse_event):
        """
        Ungrab widget.
        """
        self._is_grabbed = False

    def grab_update(self, mouse_event):
        """
        Update grabbed widget with incoming mouse event.
        """
