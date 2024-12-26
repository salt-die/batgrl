"""
Functions and classes for determining gadget regions.

Notes
-----
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

from .basic import Point, Size

__all__ = ["Region"]

class Region:
    """
    Collection of mutually exclusive bands of rects.

    Methods
    -------
    rects()
        Yield position and size of rects that make up the region.
    from_rect(pos, size)
        Return a new region from a rect position and size.
    """

    def __and__(self, other: Region) -> Region:
        """Return the intersection of self and other."""

    def __or__(self, other: Region) -> Region:
        """Return the union of self and other."""

    def __add__(self, other: Region) -> Region:
        """Return the union of self and other."""

    def __sub__(self, other: Region) -> Region:
        """Return the difference of self and other."""

    def __xor__(self, other: Region) -> Region:
        """Return the symmetric difference of self and other."""

    def __bool__(self) -> bool:
        """Whether region is non-empty."""

    def __eq__(self, other: Region) -> bool:
        """Whether two regions are equal."""

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
    def from_rect(cls, pos: Point, size: Size) -> Region:
        """
        Return a region from a rect position and size.

        Returns
        -------
        Region
            A new region.
        """
