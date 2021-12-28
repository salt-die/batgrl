from enum import Enum
from typing import NamedTuple

__all__ = "Rect", "Anchor", "PosHint", "SizeHint"


class Rect(NamedTuple):
    top: int
    left: int
    bottom: int
    right: int
    height: int
    width: int


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


class PosHint(NamedTuple):
    y: float | None
    x: float | None


class SizeHint(NamedTuple):
    height: float | None
    width: float | None

