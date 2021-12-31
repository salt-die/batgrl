from enum import Enum
from typing import NamedTuple

__all__ = "SizeHint", "PosHint", "Anchor"


class SizeHint(NamedTuple):
    height: float | None
    width: float | None


class PosHint(NamedTuple):
    y: float | None
    x: float | None


class Anchor(str, Enum):
    CENTER = "CENTER"
    LEFT_CENTER = "LEFT_CENTER"
    RIGHT_CENTER = "RIGHT_CENTER"
    TOP_LEFT = "TOP_LEFT"
    TOP_CENTER = "TOP_CENTER"
    TOP_RIGHT = "TOP_RIGHT"
    BOTTOM_LEFT = "BOTTOM_LEFT"
    BOTTOM_CENTER = "BOTTOM_CENTER"
    BOTTOM_RIGHT = "BOTTOM_RIGHT"
