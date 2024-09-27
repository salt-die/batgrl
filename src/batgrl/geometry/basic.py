"""Basic geometry functions and types."""

from __future__ import annotations

from numbers import Real
from typing import NamedTuple, Self

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "clamp",
    "lerp",
    "points_on_circle",
    "round_down",
    "rect_slice",
    "Point",
    "Size",
]


def clamp(value: Real, min: Real | None, max: Real | None) -> Real:
    """
    If ``value`` is less than ``min``, returns ``min``; else if ``max`` is less than
    ``value``, returns ``max``; else returns ``value``. A one-sided clamp is possible
    by setting ``min`` or ``max`` to ``None``.

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
    """Linear interpolation of `a` to `b` with proportion `p`."""
    return (1.0 - p) * a + p * b


def points_on_circle(
    n: int,
    radius: float = 1.0,
    center: tuple[float, float] = (0.0, 0.0),
    offset: float = 0.0,
) -> NDArray[np.float32]:
    """
    Return `n` points on a circle.

    Parameters
    ----------
    n : int
        Number of points on a circle.
    radius : float, default: 1.0
        Radius of circle.
    center : tuple[float, float], default: (0.0, 0.0)
        Center of circle.
    offset : float, default: 0.0
        Rotate output points by `offset` radians.

    Returns
    -------
    NDArray[np.float32]
        An `(n, 2)`-shaped NDArray of points on a circle.
    """
    angles = np.linspace(0, 2 * np.pi, endpoint=False, num=n) + offset
    return radius * np.stack([np.sin(angles), np.cos(angles)]).T + center


def rect_slice(pos: Point, size: Size) -> tuple[slice, slice]:
    """
    Return slices for indexing a rect in a numpy array.

    Parameters
    ----------
    pos : Point
        Position of rect.
    size : Size
        Size of rect.

    Returns
    -------
    tuple[slice, slice]
        Slices that index a rect in a numpy array.
    """
    y, x = pos
    h, w = size
    return slice(y, y + h), slice(x, x + w)


def round_down(n: float) -> int:
    """
    Like the built-in `round`, but always rounds down.

    Used instead of `round` for smoother geometry.
    """
    i, r = divmod(n, 1)
    if r <= 0.5:
        return int(i)
    return int(i) + 1


class Point(NamedTuple):
    """
    A 2-d point.

    Note that y-coordinate is before x-coordinate. This convention is used so that the
    2-d arrays that underly a gadget's data can be directly indexed with the point.

    Parameters or attributes type-hinted `Point` can often take `tuple[int, int]` for
    convenience.

    Parameters
    ----------
    y : int
        y-coordinate of point.
    x : int
        x-coordinate of point.

    Attributes
    ----------
    y : int
        y-coordinate of point.
    x : int
        x-coordinate of point.
    """

    y: int
    """y-coordinate of point."""
    x: int
    """x-coordinate of point."""

    def __add__(self, other: Self) -> Self:
        y, x = self
        oy, ox = other

        return type(self)(y + oy, x + ox)

    def __radd__(self, other: Self) -> Self:
        oy, ox = other
        y, x = self
        return type(self)(oy + y, ox + x)

    def __sub__(self, other: Self) -> Self:
        y, x = self
        oy, ox = other
        return type(self)(y - oy, x - ox)

    def __rsub__(self, other: Self) -> Self:
        oy, ox = other
        y, x = self
        return type(self)(oy - y, ox - x)

    def __neg__(self) -> Self:
        y, x = self
        return type(self)(-y, -x)


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
    center : Point
        Center of area.
    """

    height: int
    """Height of area."""
    width: int
    """Width of area."""

    @property
    def rows(self) -> int:
        """Alias for height."""
        return self.height

    @property
    def columns(self) -> int:
        """Alias for width."""
        return self.width

    def __contains__(self, point: Point) -> bool:
        """Whether a point is within the rectangle."""
        y, x = point
        h, w = self
        return 0 <= y < h and 0 <= x < w

    @property
    def center(self) -> Point:
        """Center of area."""
        h, w = self
        return Point(h // 2, w // 2)
