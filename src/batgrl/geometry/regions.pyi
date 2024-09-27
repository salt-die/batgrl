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

from collections.abc import Iterator
from typing import Self

from .basic import Point, Size

__all__ = ["Region"]

class _Band:
    """A row of mutually exclusive rects."""

    y1: int
    """The y-coordinate of the top of the band."""
    y2: int
    """The y-coordinate of the bottom of the band."""
    walls: list[int]
    """
    Each contiguous pair of ints in `walls` represent the left and right side of a rect
    in the band.
    """

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

    bands: list[_Band]
    """Bands that make up the region."""

    def __and__(self, other: Self) -> Self:
        """Return the intersection of self and other."""

    def __or__(self, other: Self) -> Self:
        """Return the union of self and other."""

    def __add__(self, other: Self) -> Self:
        """Return the union of self and other."""

    def __sub__(self, other: Self) -> Self:
        """Return the difference of self and other."""

    def __xor__(self, other: Self) -> Self:
        """Return the symmetric difference of self and other."""

    def __bool__(self) -> bool:
        """Whether region is non-empty."""

    def __contains__(self, point: Point) -> bool:
        """Return whether point is in region."""

    def rects(self) -> Iterator[tuple[Point, Size]]:
        """
        Yield position and size of rects that make up the region.

        Yields
        ------
        tuple[Point, Size]
            A position and size of a rect in the region.
        """

    @classmethod
    def from_rect(cls, pos: Point, size: Size) -> Self:
        """
        Return a region from a rect position and size.

        Returns
        -------
        Region
            A new region.
        """
