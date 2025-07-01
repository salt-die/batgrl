"""Data structures and functions for :mod:`batgrl` geometry."""

from .basic import (
    Point,
    Pointlike,
    Size,
    Sizelike,
    clamp,
    lerp,
    normalize,
    points_on_circle,
    rect_slice,
    round_down,
)
from .easings import EASINGS, Easing
from .motion import BezierCurve, move_along_path
from .regions import Region

__all__ = [
    "EASINGS",
    "BezierCurve",
    "Easing",
    "Point",
    "Pointlike",
    "Region",
    "Size",
    "Sizelike",
    "clamp",
    "lerp",
    "move_along_path",
    "normalize",
    "points_on_circle",
    "rect_slice",
    "round_down",
]
