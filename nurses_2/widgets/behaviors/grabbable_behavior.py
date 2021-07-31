from ...mouse import MouseEventType


class GrabbableBehavior:
    """
    Grabbable behavior for a widget. Mouse down events that collide with widget
    will "grab" it, calling the `grab` method (which may set the `is_grabbed` flag to True).
    While grabbed, each mouse event will call `grab_update` until the widget is ungrabbed,
    i.e., a mouse up event is received.
    """
    is_grabbable = True
    is_grabbed = False

    def on_click(self, mouse_event):
        if not (self.collides_coords(mouse_event.position) or self.is_grabbed):
            return super().on_click(mouse_event)

        if self.is_grabbed:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self.ungrab(mouse_event)
            else:
                self.grab_update(mouse_event)
        else:
            if self.is_grabbable and mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                self.grab(mouse_event)
            else:
                return super().on_click(mouse_event)

        return True

    def grab(self, mouse_event):
        """
        Grab widget.
        """
        self.is_grabbed = True

    def ungrab(self, mouse_event):
        """
        Ungrab widget.
        """
        self.is_grabbed = False

    def grab_update(self, mouse_event):
        """
        Update grabbed widget with incoming mouse event.
        """