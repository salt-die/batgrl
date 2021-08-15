from ..mouse import MouseEventType
from ..utils import clamp
from .widget import Widget
from .behaviors.grabbable_behavior import GrabbableBehavior


class Scatter(GrabbableBehavior, Widget):
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
    def __init__(self, *args, disable_oob=False, disable_ptf=False, **kwargs):
        super().__init__(*args, **kwargs)
        self.disable_oob = disable_oob
        self.disable_ptf = disable_ptf

        self._grabbed_child = None

    def grab(self, mouse_event):
        for child in reversed(self.children):
            if child.collides_coords(mouse_event.position):
                self._grabbed_child = child

                if not self.disable_ptf:
                    self.pull_to_front(child)

                super().grab(mouse_event)
                return True

        return False

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self._grabbed_child = None

        return True

    def grab_update(self, mouse_event):
        grabbed = self._grabbed_child
        if grabbed is None:
            return False

        grabbed.top += self.mouse_dy
        grabbed.left += self.mouse_dx

        if self.disable_oob:
            grabbed.top = clamp(grabbed.top, 0, self.height - grabbed.height)
            grabbed.left = clamp(grabbed.left, 0, self.width - grabbed.width)

        return True
