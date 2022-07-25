"""
Data structures for :mod:`nurses_2`.
"""
from typing import NamedTuple

__all__ = "Point", "Size"


class Point(NamedTuple):
    """
    A 2-d point.

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
    x: int


class Size(NamedTuple):
    """
    A 2-d size.

    Parameters
    ----------
    height : int
        Height component of size.
    width : int
        Width component of size.
    rows : int
        Alias for height.
    columns : int
        Alias for width.

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

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
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
