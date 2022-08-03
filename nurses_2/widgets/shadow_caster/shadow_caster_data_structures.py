"""
Data structures for :class:`nurses_2.widgets.shadow_caster.ShadowCaster`.
"""
from enum import Enum
from typing import NamedTuple

import numpy as np

from ...colors import Color
from ...data_structures import Point, Size
from ..widget import intersection, Rect


class Camera:
    """
    The camera determines the visible portion of the map.

    Parameters
    ----------
    pos : Point
        The position of the upper-left corner of the camera on the map.
    size : Size
        Size of the camera.

    Methods
    -------
    get_submap:
        Get the section of the map visible by the camera.

    Notes
    -----
    Submap values for areas of the camera that are out-of-bounds of the map
    will be zero.
    """
    __slots__ = "pos", "size"

    def __init__(self, pos: Point, size: Size):
        self.pos = pos
        self.size = size

    def get_submap(self, map: np.ndarray) -> np.ndarray:
        """
        Get the section of a map visible by the camera.
        """
        submap = np.zeros(self.size, dtype=np.uint8)

        mh, mw = map.shape
        h, w = self.size
        t, l = self.pos
        b, r = h + t, w + l

        dest = Rect(t, b, l, r)
        source = Rect(0, mh, 0, mw)

        if (slices := intersection(dest, source)) is not None:
            dest_slice, source_slice = slices
            submap[dest_slice] = map[source_slice]

        return submap


class Interval(NamedTuple):
    """
    A continuous interval.

    Parameters
    ----------
    start : float
        Start of interval.
    end : float
        End of interval.

    Attributes
    ----------
    start : float
        Start of interval.
    end : float
        End of interval.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    start: float
    end: float

    def __contains__(self, item: float) -> bool:
        return self.start <= item <= self.end

    def __gt__(self, other):
        if isinstance(other, (float, int)):
            return other < self.start

        return (other.start, other.end) < (self.start, self.end)


class LightIntensity(NamedTuple):
    """
    Intensity of light in three color channels.
    Each value should be between `0` and `1`.

    Parameters
    ----------
    r : float
        Red component.
    g : float
        Green component.
    b : float
        Blue component.

    Attributes
    ----------
    r : float
        Red component.
    g : float
        Green component.
    b : float
        Blue component.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    r: float
    g: float
    b: float

    @classmethod
    def from_color(self, color: Color):
        r, g, b = color
        return LightIntensity(r / 255, g / 255, b / 255)


class Coordinates(NamedTuple):
    """
    Two-dimensional coordinates.

    Parameters
    ----------
    y : float
        Y-coordinate.
    x : float
        X-coordinate.

    Attributes
    ----------
    y : float
        Y-coordinate.
    x : float
        X-coordinate.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    y: float
    x: float


class LightSource:
    """
    A light source.

    Parameters
    ----------
    coords : Coordinates, default: Coordinates(0.0, 0.0)
        Coordinates of light source on map.
    intensity : Color | LightIntensity, default: LightIntensity(0.0, 0.0, 0.0)
        Intensity of light source. If a :class:`nurses_2.colors.Color` is given it will
        be converted to an intensity with :meth:`LightIntensity.from_color`.

    Attributes
    ----------
    coords : Coordinates
        Coordinates of light source on map.
    intensity : LightIntensity
        Intensity of light source. If set with a :class:`nurses_2.colors.Color`, it will
        be converted to an intensity with :meth:`LightIntensity.from_color`.
    """
    __slots__ = "coords", "_intensity"

    def __init__(
        self,
        coords: Coordinates=Coordinates(0.0, 0.0),
        intensity: Color | LightIntensity=LightIntensity(0.0, 0.0, 0.0),
    ):
        self.coords = coords
        self.intensity = intensity

    @property
    def intensity(self) -> LightIntensity:
        return self._intensity

    @intensity.setter
    def intensity(self, intensity: Color | LightIntensity):
        if isinstance(intensity, Color):
            self._intensity = LightIntensity.from_color(intensity)
        else:
            self._intensity = intensity


class Restrictiveness(str, Enum):
    """
    The restrictiveness of the shadow caster.

    :class:`Restrictiveness` is one of "permissive", "moderate", "restrictive".

    For "permissive", any interval is visible as long as any of it's start,
    center, or end points are visible. For "moderate", the center and
    either end must be visible. For "restrictive", all points in the
    interval must be visible.
    """
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    RESTRICTIVE = "restrictive"
