from enum import Enum


class Anchor(str, Enum):
    CENTER = "CENTER"
    TOP_LEFT = "TOP_LEFT"
    TOP_RIGHT = "TOP_RIGHT"
    BOTTOM_LEFT = "BOTTOM_LEFT"
    BOTTOM_RIGHT = "BOTTOM_RIGHT"


class AutoPositionBehavior:
    """
    Re-position anchor to some percentage of parent's height / width
    (given by `pos_hint`) when parent is resized.

    Parameters
    ----------
    anchor : Anchor, default: Anchor.TOP_LEFT
        The part of this widget anchored to the pos_hint.
    pos_hint : tuple[float | None, float | None], default: (0.0, 0.0)
        The location of the anchor as a percentage parent's dimensions.
        None indicates top or left attribute will be used normally.
    """
    def __init__(self, *args, anchor=Anchor.TOP_LEFT, pos_hint=(0.0, 0.0), **kwargs):
        self.anchor = anchor
        self.top_hint, self.left_hint = pos_hint

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        anchor = self.anchor

        if anchor == Anchor.TOP_LEFT:
            offset_top, offset_left = 0, 0
        elif anchor == Anchor.TOP_RIGHT:
            offset_top, offset_left = 0, self.right
        elif anchor == Anchor.BOTTOM_LEFT:
            offset_top, offset_left = self.bottom, 0
        elif anchor == Anchor.BOTTOM_RIGHT:
            offset_top, offset_left = self.bottom, self.right
        elif anchor == Anchor.CENTER:
            offset_top, offset_left = self.middle

        h, w = self.parent.dim
        top_hint = self.top_hint
        left_hint = self.left_hint

        if top_hint is not None:
            self.top = round(h * top_hint) - offset_top

        if left_hint is not None:
            self.left = round(w * left_hint) - offset_left

        super().update_geometry()
