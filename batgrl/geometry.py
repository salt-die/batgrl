"""Data structures and functions for :mod:`batgrl` geometry."""
from bisect import bisect
from dataclasses import dataclass, field
from numbers import Real
from operator import and_, or_, xor
from typing import Callable, Iterator, NamedTuple


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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
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


def sub(a: bool, b: bool) -> bool:
    """Return `a` and not `b`."""
    return a and not b


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

    Methods
    -------
    offset(point)
        Return a new Rect moved up by `point.y` and moved left by `point.x`.
    to_slices(offset=Point(0, 0))
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
        return self._merge_regions(other, and_)

    def __or__(self, other: "Region") -> "Region":
        return self._merge_regions(other, or_)

    def __add__(self, other: "Region") -> "Region":
        return self._merge_regions(other, or_)

    def __sub__(self, other: "Region") -> "Region":
        return self._merge_regions(other, sub)

    def __xor__(self, other: "Region") -> "Region":
        return self._merge_regions(other, xor)

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
