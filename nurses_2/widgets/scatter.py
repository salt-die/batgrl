from ..mouse import MouseEventType
from .widget import Widget


class Scatter(Widget):
    """
    A scatter widget. Any widget added to a Scatter can be translated by
    clicking it and dragging the mouse. Widgets will be brought to front when clicked.
    """
    _grabbed = None
    _last_mouse_pos = None

    def on_click(self, mouse_event):
        if not (self.collides_coords(mouse_event.position) or self._grabbed):
            return super().on_click(mouse_event)

        if self._grabbed is None:
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                for child in reversed(self.children):
                    if child.collides_coords(mouse_event.position):
                        self.pull_to_front(child)
                        self._grabbed = child
                        self._last_mouse_pos = mouse_event.position
                        break
            else:
                return super().on_click(mouse_event)
        else:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._grabbed = self._last_mouse_pos = None
            else:
                last_y, last_x = self._last_mouse_pos
                y, x = self._last_mouse_pos = mouse_event.position
                self._grabbed.top += y - last_y
                self._grabbed.left += x - last_x

        return True
