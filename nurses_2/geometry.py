"""
Data structures and functions for :mod:`nurses_2` geometry.
"""
from functools import lru_cache
from numbers import Real
from typing import NamedTuple


class Point(NamedTuple):
    """
    A 2-d point.

    Note that y-coordinate is before x-coordinate. This convention is used so that
    the 2-d arrays that underly a widget's data can be directly indexed with the point.

    Parameters or attributes type-hinted `Point` can often take `tuple[int, int]` for
    convenience.

    Parameters
    ----------
    y : int
        Y-coordinate of point.
    x : int
        X-coordinate of point.

    Attributes
    ----------
    y : int
        Y-coordinate of point.
    x : int
        X-coordinate of point.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """

    y: int
    """Y-coordinate of point."""
    x: int
    """X-coordinate of point."""


class Size(NamedTuple):
    """
    A rectangular area.

    Parameters or attributes type-hinted `Size` can often take `tuple[int, int]` for
    convenience.

    Parameters
    ----------
    height : int
        Height of area.
    width : int
        Width of area.

    Attributes
    ----------
    height : int
        Height of area.
    width : int
        Width of area.
    rows : int
        Alias for height.
    columns : int
        Alias for width.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """

    height: int
    """Height of area."""
    width: int
    """Width of area."""

    @property
    def rows(self):
        """
        Alias for height.
        """
        return self.height

    @property
    def columns(self):
        """
        Alias for width.
        """
        return self.width


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
    """Top-coordinate of rectangle."""
    bottom: int
    """Bottom-coordinate of rectangle."""
    left: int
    """Left-coordinate of rectangle."""
    right: int
    """Right-coordinate of rectangle."""


@lru_cache(maxsize=128)
def intersection(
    a: Rect, b: Rect
) -> tuple[tuple[slice, slice], tuple[slice, slice]] | None:
    """
    Find the intersection of this and another rect and return a pair of numpy
    indices that correspond to that intersection for each rect.

    Parameters
    ----------
    a, b : Rect
        Rects to intersect.

    Returns
    -------
    tuple[tuple[slice, slice], tuple[slice, slice]] | None
        2d numpy slices of intersection relative to each rect or `None` if a and b don't
        intersect.
    """
    btop, bbottom, bleft, bright = b
    bheight, bwidth = bbottom - btop, bright - bleft

    atop, abottom, aleft, aright = a
    atop -= btop
    abottom -= btop
    aleft -= bleft
    aright -= bleft

    if (
        atop >= bheight or abottom < 0 or aleft >= bwidth or aright < 0
    ):  # Empty intersection.
        return

    if atop < 0:
        at = -atop
        bt = 0
    else:
        at = 0
        bt = atop

    if abottom >= bheight:
        ab = bheight - atop
        bb = bheight
    else:
        ab = abottom - atop
        bb = abottom

    if aleft < 0:
        al = -aleft
        bl = 0
    else:
        al = 0
        bl = aleft

    if aright >= bwidth:
        ar = bwidth - aleft
        br = bwidth
    else:
        ar = aright - aleft
        br = aright

    return (slice(at, ab), slice(al, ar)), (slice(bt, bb), slice(bl, br))


def clamp(value: Real, min: Real | None, max: Real | None) -> Real:
    """
    If `value` is less than `min`, returns `min`; otherwise if `max` is less than
    `value`, returns `max`; otherwise returns `value`. A one-sided clamp is possible by
    setting `min` or `max` to `None`.

    Parameters
    ----------
    value : Real
        Value to clamp.
    min : Real | None
        Minimum of clamped value.
    max : Real | None
        Maximum of clamped value.

    Returns
    -------
    Real
        A value between `min` and `max`, inclusive.
    """
    if min is not None and value < min:
        return min

    if max is not None and value > max:
        return max

    return value


def lerp(a: Real, b: Real, p: Real) -> Real:
    """
    Linear interpolation of `a` to `b` with proportion `p`.
    """
    return (1.0 - p) * a + p * b
