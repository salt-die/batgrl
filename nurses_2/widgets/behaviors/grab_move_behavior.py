from ...clamp import clamp
from .grabbable_behavior import GrabbableBehavior


class GrabMoveBehavior(GrabbableBehavior):
    """
    Draggable behavior for a widget. Translate a widget by clicking and dragging it.

    Parameters
    ----------
    disable_oob : bool, default: False
        If true, widget won't be translated outside of its parent's bounding box.
    allow_vertical_translation : bool, default: True
        Allow vertical translation.
    allow_horizontal_translation : bool, default: True
        Allow horizontal translation.
    """
    def __init__(
        self,
        *,
        disable_oob=False,
        allow_vertical_translation=True,
        allow_horizontal_translation=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.disable_oob = disable_oob
        self.allow_vertical_translation = allow_vertical_translation
        self.allow_horizontal_translation = allow_horizontal_translation

    def grab_update(self, mouse_event):
        if self.allow_vertical_translation:
            self.top += self.mouse_dy
        if self.allow_horizontal_translation:
            self.left += self.mouse_dx

        if self.disable_oob:
            self.top = clamp(self.top, 0, self.parent.height - self.height)
            self.left = clamp(self.left, 0, self.parent.width - self.width)
