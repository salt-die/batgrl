"""
Data structures for `nurses_2`.
"""
from typing import NamedTuple

__all__ = "Point", "Size"


class Point(NamedTuple):
    """
    A 2-d point.

    Attributes
    ----------
    y : int
        Y-coordinate of point.
    x : int
        X - coordinate of point.
    """
    y: int
    x: int


class Size(NamedTuple):
    """
    A 2-d size.

    Attributes
    ----------
    height : int
        Height component of size.
    width : int
        Width component of size.
    rows : int
        Alias for height.
    columns : int
        Alias for width.
    """
    height: int
    width: int

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
