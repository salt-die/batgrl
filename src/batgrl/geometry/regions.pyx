"""
Functions and classes for determining gadget regions.

A gadget's region is calculated as a first step in compositing to determine its visible
area in the terminal.

Let's say we have the following gadgets:

.. code-block:: text

    +--------+------+---------+
    |        |  B   |         |
    |        +------+         |
    |                         |
    |        A             +-------+
    |                      |   C   |
    +----------------------+-------+

And we want to represent the visible region of ``A``:

.. code-block:: text

    +--------+      +---------+
    |        |      |         |
    |        +------+         |
    |                         |
    |                      +--+
    |                      |
    +----------------------+

One method is to divide the area into a series of mutually exclusive horizontal bands:

.. code-block:: text

    +--------+      +---------+
    | a      | b    | c       | d    - Top band with walls at a, b, c, d
    |--------+------+---------+
    | e                       | f    - Middle band with walls at e, f
    +----------------------+--+
    | g                    | h       - Bottom band with walls at g, h
    +----------------------+

Walls are the x-coordinates of the rects in a band. Two contiguous walls indicate a new
rect. Bands are a sorted list of walls with each band having a top y-coordinate and
bottom y-coordinate. And finally, Regions are a sorted list of non-intersecting Bands.
"""

from bisect import bisect
from collections.abc import Iterator
from typing import Self

import cython

from .basic import Point, Size

__all__ = ["Region"]


@cython.dataclasses.dataclass
class _Band:
    """A row of mutually exclusive rects."""

    y1: cython.int
    """The y-coordinate of the top of the band."""
    y2: cython.int
    """The y-coordinate of the bottom of the band."""
    walls: list[cython.int]
    """
    Each contiguous pair of ints in `walls` represent the left and right side of a rect
    in the band.
    """


ctypedef bint (*bool_op)(bint, bint)


cdef bint _bint_or(bint a, bint b):
    return a | b


cdef bint _bint_and(bint a, bint b):
    return a & b


cdef bint _bint_xor(bint a, bint b):
    return a ^ b


cdef bint _bint_sub(bint a, bint b):
    return a & (1 - b)


cdef list[cython.int] _merge(list[cython.int] a, list[cython.int] b, bool_op op):
    """Merge the walls of two bands given a set operation."""
    cdef cython.int i = 0
    cdef cython.int j = 0
    cdef cython.int threshold
    cdef bint inside_a = 0
    cdef bint inside_b = 0
    cdef bint inside_region = 0
    cdef list[cython.int] walls = []

    while i < len(a) or j < len(b):
        if i >= len(a):
            threshold = b[j]
            inside_b ^= 1
            j += 1
        elif j >= len(b):
            threshold = a[i]
            inside_a ^= 1
            i += 1
        elif a[i] < b[j]:
            threshold = a[i]
            inside_a ^= 1
            i += 1
        elif b[j] < a[i]:
            threshold = b[j]
            inside_b ^= 1
            j += 1
        else:
            threshold = a[i]
            inside_a ^= 1
            inside_b ^= 1
            i += 1
            j += 1

        if op(inside_a, inside_b) != inside_region:
            inside_region ^= 1
            walls.append(threshold)

    return walls


cdef _coalesce(bands: list[_Band]):
    """Remove empty bands and join contiguous bands with the same walls."""
    cdef cython.int i = 0
    cdef _Band a
    cdef _Band b

    while i < len(bands) - 1:
        a = bands[i]
        b = bands[i + 1]

        if len(a.walls) == 0:
            del bands[i]
        elif len(b.walls) == 0:
            del bands[i + 1]
        elif b.y1 <= a.y2 and a.walls == b.walls:
            a.y2 = b.y2
            del bands[i + 1]
        else:
            i += 1


cdef list[_Band] _merge_regions(list[_Band] a, list[_Band] b, bool_op op):
    cdef list[_Band] bands = []
    cdef cython.int i = 0
    cdef cython.int j = 0

    cdef cython.int scanline = 0
    if len(a) > 0:
        if len(b) > 0:
            scanline = min(a[0].y1, b[0].y1)
        else:
            scanline = a[0].y1
    elif len(b) > 0:
        scanline = b[0].y1

    cdef _Band r
    cdef _Band s

    while i < len(a) and j < len(b):
        r = a[i]
        s = b[j]

        if r.y1 <= s.y1:
            if scanline < r.y1:
                scanline = r.y1
            if r.y2 <= s.y1:
                bands.append(_Band(scanline, r.y2, _merge(r.walls, [], op)))
                i += 1
            else:
                if scanline < s.y1:
                    bands.append(_Band(scanline, s.y1, _merge(r.walls, [], op)))
                if r.y2 <= s.y2:
                    bands.append(_Band(s.y1, r.y2, _merge(r.walls, s.walls, op)))
                    i += 1
                    if r.y2 == s.y2:
                        j += 1
                else:
                    bands.append(_Band(s.y1, s.y2, _merge(r.walls, s.walls, op)))
                    j += 1
        else:
            if scanline < s.y1:
                scanline = s.y1
            if s.y2 <= r.y1:
                bands.append(_Band(scanline, s.y2, _merge([], s.walls, op)))
                j += 1
            else:
                if scanline < r.y1:
                    bands.append(_Band(scanline, r.y1, _merge([], s.walls, op)))
                if s.y2 <= r.y2:
                    bands.append(_Band(r.y1, s.y2, _merge(r.walls, s.walls, op)))
                    j += 1
                    if s.y2 == r.y2:
                        i += 1
                else:
                    bands.append(_Band(r.y1, r.y2, _merge(r.walls, s.walls, op)))
                    i += 1
        
        scanline = bands[-1].y2

    while i < len(a):
        r = a[i]
        if scanline < r.y1:
            scanline = r.y1
        bands.append(_Band(scanline, r.y2, _merge(r.walls, [], op)))
        i += 1

    while j < len(b):
        s = b[j]
        if scanline < s.y1:
            scanline = s.y1
        bands.append(_Band(scanline, s.y2, _merge([], s.walls, op)))
        j += 1

    _coalesce(bands)
    return bands


@cython.dataclasses.dataclass
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

    Methods
    -------
    rects()
        Yield position and size of rects that make up the region.
    from_rect(pos, size)
        Return a new region from a rect position and size.
    """
    bands: list[_Band] = cython.dataclasses.field(default_factory=list)

    def __and__(self, other: Self) -> Self:
        """Return the intersection of self and other."""
        return Region(_merge_regions(self.bands, other.bands, _bint_and))

    def __or__(self, other: Self) -> Self:
        """Return the union of self and other."""
        return Region(_merge_regions(self.bands, other.bands, _bint_or))

    def __add__(self, other: Self) -> Self:
        """Return the union of self and other."""
        return Region(_merge_regions(self.bands, other.bands, _bint_or))

    def __sub__(self, other: Self) -> Self:
        """Return the subtraction of self and other."""
        return Region(_merge_regions(self.bands, other.bands, _bint_sub))

    def __xor__(self, other: Self) -> Self:
        """Return the symmetric difference of self and other."""
        return Region(_merge_regions(self.bands, other.bands, _bint_xor))

    def __bool__(self) -> bool:
        """Whether region is non-empty."""
        return len(self.bands) > 0

    def __contains__(self, point: Point) -> bool:
        """Return whether point is in region."""
        y, x = point
        i = bisect(self.bands, y, key=lambda band: band.y1)
        if i == 0:
            return False

        band = self.bands[i - 1]
        if band.y2 <= y:
            return False

        j = bisect(band.walls, x)
        return j % 2 == 1

    def rects(self) -> Iterator[tuple[Point, Size]]:
        """
        Yield position and size of rects that make up the region.

        Yields
        ------
        tuple[Point, Size]
            A position and size of a rect in the region.
        """
        for band in self.bands:
            i = 0
            walls = band.walls
            y = band.y1
            h = band.y2 - y
            while i < len(walls):
                yield Point(y, walls[i]), Size(h, walls[i + 1] - walls[i])
                i += 2

    @classmethod
    def from_rect(cls, pos: Point, size: Size) -> Self:
        """
        Return a region from a rect position and size.

        Returns
        -------
        Region
            A new region.
        """
        y, x = pos
        h, w = size
        return cls([_Band(y, y + h, [x, x + w])])
