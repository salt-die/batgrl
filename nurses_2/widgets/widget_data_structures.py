"""
Data structures for widgets.
"""
from enum import Enum
from typing import NamedTuple

__all__ = "SizeHint", "PosHint", "Rect", "Anchor", "Easing"


class SizeHint(NamedTuple):
    """
    A size hint.

    Sets a widget's size as a proportion of parent's size.

    Parameters
    ----------
    height : float | None
        Proportion of parent's height.
    width : float | None
        Proportion of parent's width.

    Attributes
    ----------
    height : float | None
        Proportion of parent's height.
    width : float | None
        Proportion of parent's width.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    height: float | None
    width: float | None


class PosHint(NamedTuple):
    """
    A position hint.

    Sets a widget's position as a proportion of parent's size.

    Parameters
    ----------
    y : float | None
        Y-coordinate as a proportion of parent's height.
    x : float | None
        X-coordinate as a proportion of parent's width.

    Attributes
    ----------
    y : float | None
        Y-coordinate as a proportion of parent's height.
    x : float | None
        X-coordinate as a proportion of parent's width.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    y: float | None
    x: float | None


class Rect(NamedTuple):
    """
    Rectangular coordinates.

    Parameters
    ----------
    top : int
        Top-coordinate of rectangle.
    bottom : int
        Bottom-coordinate of rectangle.
    left : int
        Left-coordinate of rectangle.
    right : int
        Right-coordinate of rectangle.

    Attributes
    ----------
    top : int
        Top-coordinate of rectangle.
    bottom : int
        Bottom-coordinate of rectangle.
    left : int
        Left-coordinate of rectangle.
    right : int
        Right-coordinate of rectangle.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    top: int
    bottom: int
    left: int
    right: int


class Anchor(str, Enum):
    """
    Point of widget attached to :attr:`nurses_2.widgets.Widget.pos_hint`.

    :class:`Anchor` is one of "center", "left_center", "right_center",
    "top_left", "top_center", "top_right", "bottom_left",
    "bottom_center", "bottom_right".
    """
    CENTER = "center"
    LEFT_CENTER = "left_center"
    RIGHT_CENTER = "right_center"
    TOP_LEFT = "top_left"
    TOP_CENTER = "top_center"
    TOP_RIGHT = "top_right"
    BOTTOM_LEFT = "bottom_left"
    BOTTOM_CENTER = "bottom_center"
    BOTTOM_RIGHT = "bottom_right"


class Easing(str, Enum):
    """
    Easings for :meth:`nurses_2.widgets.Widget.tween`.
    """
    LINEAR = "linear"
    IN_QUAD = "in_quad"
    OUT_QUAD = "out_quad"
    IN_OUT_QUAD = "in_out_quad"
    IN_CUBIC = "in_cubic"
    OUT_CUBIC = "out_cubic"
    IN_OUT_CUBIC = "in_out_cubic"
    IN_QUART = "in_quart"
    OUT_QUART = "out_quart"
    IN_OUT_QUART = "in_out_quart"
    IN_QUINT = "in_quint"
    OUT_QUINT = "out_quint"
    IN_OUT_QUINT = "in_out_quint"
    IN_SINE = "in_sine"
    OUT_SINE = "out_sine"
    IN_OUT_SINE = "in_out_sine"
    IN_EXP = "in_exp"
    OUT_EXP = "out_exp"
    IN_OUT_EXP = "in_out_exp"
    IN_CIRC = "in_circ"
    OUT_CIRC = "out_circ"
    IN_OUT_CIRC = "in_out_circ"
    IN_ELASTIC = "in_elastic"
    OUT_ELASTIC = "out_elastic"
    IN_OUT_ELASTIC = "in_out_elastic"
    IN_BACK = "in_back"
    OUT_BACK = "out_back"
    IN_OUT_BACK = "in_out_back"
    IN_BOUNCE = "in_bounce"
    OUT_BOUNCE = "out_bounce"
    IN_OUT_BOUNCE = "in_out_bounce"
