from enum import Enum
from typing import NamedTuple, Optional
from warnings import warn

from .auto_resize_behavior import AutoSizeBehavior

class Anchor(str, Enum):
    CENTER = "CENTER"
    TOP_LEFT = "TOP_LEFT"
    TOP_RIGHT = "TOP_RIGHT"
    BOTTOM_LEFT = "BOTTOM_LEFT"
    BOTTOM_RIGHT = "BOTTOM_RIGHT"


class PosHint(NamedTuple):
    y: Optional[float]
    x: Optional[float]


class AutoPositionBehavior:
    """
    Position of widget is set to some proportion of parent's dimensions (given by `pos_hint`).

    Notes
    -----
    If a user widget is inheriting both AutoSizeBehavior and AutoPositionBehavior, AutoSizeBehavior should be
    before AutoPositionBehavior as positioning will require the correct dimensions of the widget.

    Parameters
    ----------
    anchor : Anchor, default: Anchor.TOP_LEFT
        The part of this widget anchored to the pos_hint.
    pos_hint : PosHint, default: (0.0, 0.0)
        The location of the anchor as a percentage parent's dimensions.
        None indicates top or left attribute will be used normally.
    """
    def __init_subclass__(cls):
        autoposition_before_autosize = False

        for parent in cls.__mro__:
            if parent is AutoSizeBehavior:
                if autoposition_before_autosize:
                    warn(
                        f"AutoPositionBehavior before AutoSizeBehavior in {cls.__name__}.__mro__."
                        " AutoSizeBehavior should be inherited before AutoPositionBehavior."
                    )
                break

            if parent is AutoPositionBehavior:
                autoposition_before_autosize = True

    def __init__(self, *args, anchor=Anchor.TOP_LEFT, pos_hint: PosHint=PosHint(0.0, 0.0), **kwargs):
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
