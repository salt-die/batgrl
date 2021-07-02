from enum import Enum


class Anchor(str, Enum):
    center = "center"
    top_left = "top_left"
    top_right = "top_right"
    bottom_left = "bottom_left"
    bottom_right = "bottom_right"


class AutoPositionBehavior:
    """
    Re-position anchor to some percentage of parent's height / width (given by `pos_hint`) when parent is resized.
    """
    def __init__(self, *args, anchor=Anchor.top_left, pos_hint=(.5, .5), **kwargs):
        self.anchor = anchor
        self.top_hint, self.left_hint = pos_hint

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        anchor = self.anchor

        if anchor == Anchor.top_left:
            offset_top, offset_left = 0, 0
        elif anchor == Anchor.top_right:
            offset_top, offset_left = 0, self.right
        elif anchor == Anchor.bottom_left:
            offset_top, offset_left = self.bottom, 0
        elif anchor == Anchor.bottom_right:
            offset_top, offset_left = self.bottom, self.right
        elif anchor == Anchor.center:
            offset_top, offset_left = self.middle

        h, w = self.parent.dim
        top_hint = self.top_hint
        left_hint = self.left_hint

        self.top = round(h * top_hint) - offset_top
        self.left = round(w * left_hint) - offset_left

        super().update_geometry()
