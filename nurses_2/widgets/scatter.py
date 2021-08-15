from ..mouse import MouseEventType
from ..utils import clamp
from .widget import Widget


class Scatter(Widget):
    """
    A scatter widget. Any widget added to a Scatter can be translated by
    clicking it and dragging the mouse. Widgets will be brought to front when clicked.

    Parameters
    ----------
    disable_oob : bool, default: False
        Disallow widgets from being translated out-of-bounds if true.
    disable_ptf : bool, default: False
        If true, widgets won't be pulled-to-front when clicked.
    """
    _grabbed = None
    _last_mouse_pos = None

    def __init__(self, *args, disable_oob=False, disable_ptf=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_oob = disable_oob
        self.disable_ptf = disable_ptf

    def on_click(self, mouse_event):
        if self._grabbed is not None:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._grabbed = self._last_mouse_pos = None
            else:
                last_y, last_x = self._last_mouse_pos
                y, x = self._last_mouse_pos = mouse_event.position

                grabbed = self._grabbed

                grabbed.top += y - last_y
                grabbed.left += x - last_x

                if self.disable_oob:
                    grabbed.top = clamp(grabbed.top, 0, self.height - grabbed.height, 0, 1)
                    grabbed.left = clamp(grabbed.left, 0, self.width - grabbed.width, 0, 1)

            return True

        if (
            self.collides_coords(mouse_event.position)
            and mouse_event.event_type == MouseEventType.MOUSE_DOWN
        ):
            for child in reversed(self.children):
                if child.collides_coords(mouse_event.position):
                    self._grabbed = child
                    self._last_mouse_pos = mouse_event.position

                    if not self.disable_ptf:
                        self.pull_to_front(child)

                    return True
