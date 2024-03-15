"""Data structures and functions for :mod:`batgrl` geometry."""
import asyncio
from bisect import bisect
from dataclasses import dataclass, field
from itertools import accumulate
from math import comb
from numbers import Real
from time import monotonic
from typing import Callable, Iterator, NamedTuple, Protocol

import numpy as np
from numpy.typing import NDArray

from .easings import EASINGS, Easing

__all__ = [
    "clamp",
    "lerp",
    "points_on_circle",
    "round_down",
    "Point",
    "Size",
    "Rect",
    "Region",
    "BezierCurve",
]


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

    Note that y-coordinate is before x-coordinate. This convention is used so that
    the 2-d arrays that underly a gadget's data can be directly indexed with the point.

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
    count(value)
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807)
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
    count(value)
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807)
        Return first index of value.
    """

    height: int
    """Height of area."""
    width: int
    """Width of area."""

    @property
    def rows(self):
        """Alias for height."""
        return self.height

    @property
    def columns(self):
        """Alias for width."""
        return self.width


@dataclass(slots=True)
class Rect:
    """
    Rectangular Coordinates.

    Parameters
    ----------
    top : int
        y-coordinate of top of rect.
    bottom : int
        y-coordinate of bottom of rect.
    left : int
        x-coordinate of left of rect.
    right : int
        x-coordinate of right of rect.

    Attributes
    ----------
    top : int
        y-coordinate of top of rect.
    bottom : int
        y-coordinate of bottom of rect.
    left : int
        x-coordinate of left of rect.
    right : int
        x-coordinate of right of rect.

    Methods
    -------
    offset(point)
        Return a new Rect moved up by `point.y` and moved left by `point.x`.
    to_slices(offset=(0, 0))
        Return slices for indexing the rect in a numpy array.
    """

    top: int
    """y-coordinate of top of rect."""
    bottom: int
    """y-coordinate of bottom of rect."""
    left: int
    """x-coordinate of left of rect."""
    right: int
    """x-coordinate of right of rect."""

    def offset(self, point: Point) -> "Rect":
        """
        Return a new Rect moved up by `point.y` and moved left by `point.x`.

        Returns
        -------
        Rect
            A new rect offset by point.
        """
        y, x = point
        return Rect(self.top - y, self.bottom - y, self.left - x, self.right - x)

    def to_slices(self, offset: Point = Point(0, 0)) -> tuple[slice, slice]:
        """
        Return slices for indexing the rect in a numpy array.

        Parameters
        ----------
        offset : Point, default: Point(0, 0)
            Move the slices up and left by offset.

        Returns
        -------
        tuple[slice, slice]
            Slices that index the rect in a numpy array.
        """
        y, x = offset
        return (
            slice(self.top - y, self.bottom - y),
            slice(self.left - x, self.right - x),
        )


@dataclass(slots=True)
class _Band:
    """A row of mutually exclusive rects."""

    y1: int
    """y-coordinate of top of band."""
    y2: int
    """y-coordinate of bottom of band."""
    walls: list[int]
    """
    Each contiguous pair of ints in `walls` represent the left and right side of a
    rect in the band.
    """

    def __gt__(self, y: int):
        """
        Whether band's y1-coordinate is greater than `y`.

        Implemented so that a list of sorted bands can be bisected by
        a y-coordinate.
        """
        return y < self.y1


def _merge(op: Callable[[bool, bool], bool], a: list[int], b: list[int]) -> list[int]:
    """Merge the walls of two bands given a set operation."""
    i = j = 0
    inside_a = inside_b = inside_region = False
    walls = []

    while i < len(a) or j < len(b):
        current_a = a[i] if i < len(a) else float("inf")
        current_b = b[j] if j < len(b) else float("inf")
        threshold = min(current_a, current_b)

        if current_a == threshold:
            inside_a = not inside_a
            i += 1

        if current_b == threshold:
            inside_b = not inside_b
            j += 1

        if op(inside_a, inside_b) != inside_region:
            inside_region = not inside_region
            walls.append(threshold)

    return walls


@dataclass(slots=True, unsafe_hash=True)
class Region:
    """
    Collection of mutually exclusive bands of rects.

    Parameters
    ----------
    bands : list[_Band], default: []
        Bands that make up the region.

    Attributes
    ----------
    bands : list[_Band]
        Bands that make up the region.

    bbox : Rect | None
        Bounding box of region.

    Methods
    -------
    rects()
        Yield rects that make up the region.
    from_rect(post, size)
        Return a new region from a rect position and size.
    """

    bands: list[_Band] = field(default_factory=list)

    def _coalesce(self):
        """Join contiguous bands with the same walls to reduce rects."""
        bands = self.bands = [band for band in self.bands if len(band.walls) > 0]

        i = 0
        while i < len(bands) - 1:
            a, b = bands[i], bands[i + 1]
            if b.y1 <= a.y2 and a.walls == b.walls:
                a.y2 = b.y2
                del bands[i + 1]
            else:
                i += 1

    def _merge_regions(
        self, other: "Region", op: Callable[[bool, bool], bool]
    ) -> "Region":
        bands = []
        i = j = 0
        scanline = -float("inf")

        while i < len(self.bands) and j < len(other.bands):
            r, s = self.bands[i], other.bands[j]
            if r.y1 <= s.y1:
                if scanline < r.y1:
                    scanline = r.y1
                if r.y2 < s.y1:
                    ## ---------------
                    ## - - - - - - - - scanline
                    ##        r
                    ## ---------------
                    ##        ~~~~~~~~~~~~~~~
                    ##               s
                    ##        ~~~~~~~~~~~~~~~
                    bands.append(_Band(scanline, r.y2, _merge(op, r.walls, [])))
                    scanline = r.y2
                    i += 1
                elif r.y2 < s.y2:
                    if scanline < s.y1:
                        ## ---------------
                        ## - - - - - - - - scanline
                        ##        r
                        ##        ~~~~~~~~~~~~~~~
                        ## ---------------
                        ##               s
                        ##        ~~~~~~~~~~~~~~~
                        bands.append(_Band(scanline, s.y1, _merge(op, r.walls, [])))
                    if s.y1 < r.y2:
                        ## ---------------
                        ##        r
                        ##        ~-~-~-~-~-~-~-~ scanline
                        ## ---------------
                        ##               s
                        ##        ~~~~~~~~~~~~~~~
                        bands.append(_Band(s.y1, r.y2, _merge(op, r.walls, s.walls)))
                    scanline = r.y2
                    i += 1
                else:  # r.y2 >= s.y2
                    if scanline < s.y1:
                        ## ---------------
                        ## - - - - - - - - scanline
                        ##        r
                        ##        ~~~~~~~~~~~~~~~
                        ##               s
                        ##        ~~~~~~~~~~~~~~~
                        ## ---------------
                        bands.append(_Band(scanline, s.y1, _merge(op, r.walls, [])))
                    ## ---------------
                    ##        r
                    ##        ~-~-~-~-~-~-~-~ scanline
                    ##               s
                    ##        ~~~~~~~~~~~~~~~
                    ## ---------------
                    bands.append(_Band(s.y1, s.y2, _merge(op, r.walls, s.walls)))
                    scanline = s.y2
                    if s.y2 == r.y2:
                        i += 1
                    j += 1
            else:  # s.y1 < r.y1
                if scanline < s.y1:
                    scanline = s.y1
                if s.y2 < r.y1:
                    ## ~~~~~~~~~~~~~~~
                    ## - - - - - - - - scanline
                    ##        s
                    ## ~~~~~~~~~~~~~~~
                    ##        _______________
                    ##               r
                    ##        _______________
                    bands.append(_Band(scanline, s.y2, _merge(op, [], s.walls)))
                    scanline = s.y2
                    j += 1
                elif s.y2 < r.y2:
                    if scanline < r.y1:
                        ## ~~~~~~~~~~~~~~~
                        ## - - - - - - - - scanline
                        ##        s
                        ##        ---------------
                        ## ~~~~~~~~~~~~~~~
                        ##               r
                        ##        ---------------
                        bands.append(_Band(scanline, r.y1, _merge(op, [], s.walls)))
                    if r.y1 < s.y2:
                        ## ~~~~~~~~~~~~~~~
                        ##        s
                        ##        --------------- scanline
                        ## ~~~~~~~~~~~~~~~
                        ##               r
                        ##        ---------------
                        bands.append(_Band(r.y1, s.y2, _merge(op, r.walls, s.walls)))
                    scanline = s.y2
                    j += 1
                else:  # s.y2 >= r.y2
                    if scanline < r.y1:
                        ## ~~~~~~~~~~~~~~~
                        ## - - - - - - - - scanline
                        ##        s
                        ##        ---------------
                        ##               r
                        ##        ---------------
                        ## ~~~~~~~~~~~~~~~
                        bands.append(_Band(scanline, r.y1, _merge(op, [], s.walls)))
                    ## ~~~~~~~~~~~~~~~
                    ##        s
                    ##        --------------- scanline
                    ##               r
                    ##        ---------------
                    ## ~~~~~~~~~~~~~~~
                    bands.append(_Band(r.y1, r.y2, _merge(op, r.walls, s.walls)))
                    scanline = r.y2
                    if r.y2 == s.y2:
                        j += 1
                    i += 1

        while i < len(self.bands):
            r = self.bands[i]
            if scanline < r.y1:
                scanline = r.y1
            bands.append(_Band(scanline, r.y2, _merge(op, r.walls, [])))
            i += 1

        while j < len(other.bands):
            s = other.bands[j]
            if scanline < s.y1:
                scanline = s.y1
            bands.append(_Band(scanline, s.y2, _merge(op, [], s.walls)))
            j += 1

        region = Region(bands=bands)
        region._coalesce()
        return region

    # TODO: in-place merge and iand, ior, iadd, isub, ixor methods

    def __and__(self, other: "Region") -> "Region":
        return self._merge_regions(other, lambda a, b: a & b)

    def __or__(self, other: "Region") -> "Region":
        return self._merge_regions(other, lambda a, b: a | b)

    def __add__(self, other: "Region") -> "Region":
        return self._merge_regions(other, lambda a, b: a | b)

    def __sub__(self, other: "Region") -> "Region":
        return self._merge_regions(other, lambda a, b: a & (not b))

    def __xor__(self, other: "Region") -> "Region":
        return self._merge_regions(other, lambda a, b: a ^ b)

    def __bool__(self):
        return len(self.bands) > 0

    @property
    def bbox(self) -> Rect | None:
        """Bounding box of region."""
        if not self:
            return None

        left = min(band.walls[0] for band in self.bands)
        right = max(band.walls[-1] for band in self.bands)

        return Rect(self.bands[0].y1, self.bands[-1].y2, left, right)

    def rects(self) -> Iterator[Rect]:
        """
        Yield rects that make up the region.

        Yields
        ------
        Rect
            A rect in the region.
        """
        for band in self.bands:
            i = 0
            while i < len(band.walls):
                yield Rect(band.y1, band.y2, band.walls[i], band.walls[i + 1])
                i += 2

    @classmethod
    def from_rect(cls, pos: Point, size: Size) -> "Region":
        """
        Return a region from a rect position and size.

        Returns
        -------
        Region
            A new region.
        """
        y, x = pos
        h, w = size
        return cls([_Band(y, y + h, (x, x + w))])

    def __contains__(self, point: Point) -> bool:
        """Whether point is in region."""
        y, x = point
        i = bisect(self.bands, y)
        if i == 0:
            return False

        band = self.bands[i - 1]
        if band.y2 <= y:
            return False

        j = bisect(band.walls, x)
        return j % 2 == 1


@dataclass
class BezierCurve:
    """
    A Bezier curve.

    Parameters
    ----------
    control_points : NDArray[np.float32]
        Array of control points of Bezier curve with shape `(N, 2)`.
    arc_length_approximation : int, default: 50
        Number of evaluations for arc length approximation.

    Attributes
    ----------
    arc_length : float
        Approximate length of Bezier curve.
    arc_length_approximation : int
        Number of evaluations for arc length approximation.
    arc_lengths : NDArray[np.float32]
        Approximate arc lengths along Bezier curve.
    coef : NDArray[np.float32]
        Binomial coefficients of Bezier curve.
    control_points : NDArray[np.float32]
        Array of control points of Bezier curve with shape `(N, 2)`.
    degree : int
        Degree of Bezier curve.

    Methods
    -------
    evaluate(t)
        Evaluate the Bezier curve at `t` (0 <= t <= 1).
    arc_length_proportion(p)
        Evaluate the Bezier curve at a proportion of its total arc length.
    """

    control_points: NDArray[np.float32]
    """Array of control points of Bezier curve with shape `(N, 2)`."""
    arc_length_approximation: int = 50
    """Number of evaluations for arc length approximation."""

    def __post_init__(self):
        if self.degree == -1:
            raise ValueError("There must be at least one control point.")

        self.coef: NDArray[np.float32] = np.array(
            [comb(self.degree, i) for i in range(self.degree + 1)], dtype=float
        )
        """Binomial coefficients of Bezier curve."""

        evaluated = self.evaluate(np.linspace(0, 1, self.arc_length_approximation))
        norms = np.linalg.norm(evaluated[1:] - evaluated[:-1], axis=-1)
        self.arc_lengths: NDArray[np.float32] = np.append(0, norms.cumsum())
        """Approximate arc lengths along Bezier curve."""

    @property
    def degree(self) -> int:
        """Degree of Bezier curve."""
        return len(self.control_points) - 1

    @property
    def arc_length(self) -> float:
        """Approximate length of Bezier curve."""
        return self.arc_lengths[-1]

    def evaluate(self, t: float | NDArray[np.float32]) -> NDArray[np.float32]:
        """Evaluate the Bezier curve at `t` (0 <= t <= 1)."""
        t = np.asarray(t)
        terms = np.logspace(0, self.degree, num=self.degree + 1, base=t).T
        terms *= np.logspace(self.degree, 0, num=self.degree + 1, base=1 - t).T
        terms *= self.coef
        return terms @ self.control_points

    def arc_length_proportion(self, p: float) -> NDArray[np.float32]:
        """Evaluate the Bezier curve at a proportion of its total arc length."""
        target_length = self.arc_length * p
        n = self.arc_length_approximation
        i = clamp(bisect(self.arc_lengths, target_length) - 1, 0, n - 1)

        previous_length = self.arc_lengths[i]
        if previous_length == target_length:
            return self.evaluate(i / n)

        target_dif = target_length - previous_length
        if i < n - 1:
            arc_dif = self.arc_lengths[i + 1] - previous_length
        else:
            arc_dif = previous_length - self.arc_lengths[i - 1]

        t = (i + target_dif / arc_dif) / n
        return self.evaluate(t)


class HasPos(Protocol):
    """An object with a position."""

    pos: Point


async def move_along_path(
    has_pos: HasPos,
    path: list[BezierCurve],
    *,
    speed: float = 1.0,
    easing: Easing = "linear",
    on_start: Callable[[], None] | None = None,
    on_progress: Callable[[float], None] | None = None,
    on_complete: Callable[[], None] | None = None,
):
    """
    Move `has_pos` along a path of Bezier curves at some speed (in cells per second).

    Parameters
    ----------
    has_pos : HasPos
        Object to be moved along path.
    path : list[BezierCurve]
        A path made up of Bezier curves.
    speed : float, default: 1.0
        Speed of movement in approximately cells per second.
    on_start : Callable[[], None] | None, default: None
        Called when motion starts.
    on_progress : Callable[[float], None] | None, default: None
        Called as motion updates with current progress.
    on_complete : Callable[[], None] | None, default: None
        Called when motion completes.
    """
    cumulative_arc_lengths = [
        *accumulate((curve.arc_length for curve in path), initial=0)
    ]
    total_arc_length = cumulative_arc_lengths[-1]
    easing_function = EASINGS[easing]
    has_pos.pos = path[0].evaluate(0.0)
    last_time = monotonic()
    distance_traveled = 0.0

    if on_start is not None:
        on_start()

    while True:
        await asyncio.sleep(0)

        current_time = monotonic()
        elapsed = current_time - last_time
        last_time = current_time
        distance_traveled += speed * elapsed
        if distance_traveled >= total_arc_length:
            has_pos.pos = path[-1].evaluate(1.0)
            break

        p = easing_function(distance_traveled / total_arc_length)
        eased_distance = p * total_arc_length

        i = clamp(bisect(cumulative_arc_lengths, eased_distance) - 1, 0, len(path) - 1)
        distance_on_curve = eased_distance - cumulative_arc_lengths[i]
        curve_p = distance_on_curve / path[i].arc_length
        has_pos.pos = path[i].arc_length_proportion(curve_p)

        if on_progress is not None:
            on_progress(p)

    if on_complete is not None:
        on_complete()
