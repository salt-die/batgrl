"""
Data structures and functions for :mod:`nurses_2` geometry.
"""
from dataclasses import dataclass, field
from numbers import Real
from operator import and_, or_, xor
from typing import Callable, Iterator, NamedTuple


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


_NO_WALLS = []  # We keep around an empty list to pass to _merge.
BoolOp = Callable[[bool, bool], bool]


def sub(a: bool, b: bool) -> bool:
    """
    `a` and not `b`
    """
    return a and not b


def _merge(op: BoolOp, a: list[int], b: list[int]) -> list[int]:
    """
    Merge the walls of two bands given a set operation.
    """
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


@dataclass(slots=True)
class Index:
    top: int
    bottom: int
    left: int
    right: int

    def to_slices(self, offset: Point = Point(0, 0)) -> tuple[slice, slice]:
        offset_y, offset_x = offset
        return (
            slice(self.top - offset_y, self.bottom - offset_y),
            slice(self.left - offset_x, self.right - offset_x),
        )


@dataclass(slots=True)
class Band:
    """
    A row of mutually exclusive rects.
    """

    y1: int
    y2: int
    walls: list[int]

    def __post_init__(self):
        if self.y2 <= self.y1:
            raise ValueError(
                f"Invalid Band: y1 ({self.y1}) is not smaller than y2 ({self.y2})"
            )


@dataclass(slots=True)
class Region:
    """
    Collection of mutually exclusive bands of rects.
    """

    bands: list[Band] = field(default_factory=list)

    def _coalesce(self):
        """
        Join contiguous bands with the same walls to reduce rects.
        """
        bands = self.bands
        i = 0
        while i < len(bands) - 1:
            a, b = bands[i], bands[i + 1]
            if len(a.walls) == 0:
                del bands[i]
            elif len(b.walls) == 0:
                del bands[i + 1]
            elif b.y1 <= a.y2 and a.walls == b.walls:
                a.y2 = b.y2
                del bands[i + 1]
            else:
                i += 1

    def _merge_regions(self, other: "Region", op: BoolOp) -> "Region":
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
                    bands.append(Band(scanline, r.y2, _merge(op, r.walls, _NO_WALLS)))
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
                        bands.append(
                            Band(scanline, s.y1, _merge(op, r.walls, _NO_WALLS))
                        )
                    if s.y1 < r.y2:
                        ## ---------------
                        ##        r
                        ##        ~-~-~-~-~-~-~-~ scanline
                        ## ---------------
                        ##               s
                        ##        ~~~~~~~~~~~~~~~
                        bands.append(Band(s.y1, r.y2, _merge(op, r.walls, s.walls)))
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
                        bands.append(
                            Band(scanline, s.y1, _merge(op, r.walls, _NO_WALLS))
                        )
                    ## ---------------
                    ##        r
                    ##        ~-~-~-~-~-~-~-~ scanline
                    ##               s
                    ##        ~~~~~~~~~~~~~~~
                    ## ---------------
                    bands.append(Band(s.y1, s.y2, _merge(op, r.walls, s.walls)))
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
                    bands.append(Band(scanline, s.y2, _merge(op, _NO_WALLS, s.walls)))
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
                        bands.append(
                            Band(scanline, r.y1, _merge(op, _NO_WALLS, s.walls))
                        )
                    if r.y1 < s.y2:
                        ## ~~~~~~~~~~~~~~~
                        ##        s
                        ##        --------------- scanline
                        ## ~~~~~~~~~~~~~~~
                        ##               r
                        ##        ---------------
                        bands.append(Band(r.y1, s.y2, _merge(op, r.walls, s.walls)))
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
                        bands.append(
                            Band(scanline, r.y1, _merge(op, _NO_WALLS, s.walls))
                        )
                    ## ~~~~~~~~~~~~~~~
                    ##        s
                    ##        --------------- scanline
                    ##               r
                    ##        ---------------
                    ## ~~~~~~~~~~~~~~~
                    bands.append(Band(r.y1, r.y2, _merge(op, r.walls, s.walls)))
                    scanline = r.y2
                    if r.y2 == s.y2:
                        j += 1
                    i += 1

        while i < len(self.bands):
            r = self.bands[i]
            if scanline < r.y1:
                scanline = r.y1
            bands.append(Band(scanline, r.y2, _merge(op, r.walls, _NO_WALLS)))
            i += 1

        while j < len(other.bands):
            s = other.bands[j]
            if scanline < s.y1:
                scanline = s.y1
            bands.append(Band(scanline, s.y2, _merge(op, _NO_WALLS, s.walls)))
            j += 1

        region = Region(bands=bands)
        region._coalesce()
        return region

    def __and__(self, other: "Region") -> "Region":
        return self._merge_regions(other, and_)

    def __add__(self, other: "Region") -> "Region":
        return self._merge_regions(other, or_)

    def __sub__(self, other: "Region") -> "Region":
        return self._merge_regions(other, sub)

    def __xor__(self, other: "Region") -> "Region":
        return self._merge_regions(other, xor)

    def __bool__(self):
        return len(self.bands) > 0

    def indices(self) -> Iterator[Index]:
        """
        Yield indices (top, bottom, left, right) for each rect that make up the region.
        """
        for band in self.bands:
            i = 0
            while i < len(band.walls):
                yield Index(band.y1, band.y2, band.walls[i], band.walls[i + 1])
                i += 2

    @property
    def bbox_indices(self) -> Index | None:
        """
        Bounding box indices (top, bottom, left, right) of region or None if region is
        empty.
        """
        if not self:
            return None

        left = min(band.walls[0] for band in self.bands)
        right = max(band.walls[-1] for band in self.bands)

        return Index(self.bands[0].y1, self.bands[-1].y2, left, right)

    @classmethod
    def from_rect(cls, pos: Point, size: Size) -> "Region":
        y, x = pos
        h, w = size
        return cls([Band(y, y + h, [x, x + w])])
