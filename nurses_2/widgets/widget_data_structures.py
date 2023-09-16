"""
Data structures for widgets.
"""
from typing import Literal, NamedTuple

import numpy as np
from numpy.typing import NDArray

__all__ = "Char", "style_char", "SizeHint", "PosHint", "Rect", "Anchor", "Easing"

Char = np.dtype(
    [
        ("char", "U1"),
        ("bold", "?"),
        ("italic", "?"),
        ("underline", "?"),
        ("strikethrough", "?"),
        ("overline", "?"),
    ]
)
"""Data type of canvas arrays."""


def style_char(
    char: str,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    overline: bool = False,
) -> NDArray[Char]:
    """
    Return a zero-dimensional `Char` array.

    Parameters
    ----------
    char : str
        A single unicode character.
    bold : bool, default: False
        Whether char is bold.
    italic : bool, default: False
        Whether char is italic.
    underline : bool, default: False
        Whether char is underlined.
    strikethrough : bool, default: False
        Whether char is strikethrough.
    overline : bool, default: False
        Whether char is overlined.
    """
    return np.array(
        (char, bold, italic, underline, strikethrough, overline), dtype=Char
    )


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


Anchor = Literal[
    "bottom",
    "bottom-left",
    "bottom-right",
    "center",
    "left",
    "right",
    "top",
    "top-left",
    "top-right",
]
"""
Point of widget attached to :attr:`nurses_2.widgets.Widget.pos_hint`.
"""

Easing = Literal[
    "linear",
    "in_quad",
    "out_quad",
    "in_out_quad",
    "in_cubic",
    "out_cubic",
    "in_out_cubic",
    "in_quart",
    "out_quart",
    "in_out_quart",
    "in_quint",
    "out_quint",
    "in_out_quint",
    "in_sine",
    "out_sine",
    "in_out_sine",
    "in_exp",
    "out_exp",
    "in_out_exp",
    "in_circ",
    "out_circ",
    "in_out_circ",
    "in_elastic",
    "out_elastic",
    "in_out_elastic",
    "in_back",
    "out_back",
    "in_out_back",
    "in_bounce",
    "out_bounce",
    "in_out_bounce",
]
"""Easings for :meth:`nurses_2.widgets.Widget.tween`"""
