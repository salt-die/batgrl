from enum import Enum
from typing import NamedTuple

import numpy as np

from ...colors import Color
from ...data_structures import Point, Size


class Camera:
    """
    The camera determines the visible portion of the map.

    Parameters
    ----------
    pos : Point
        The position of the upper-left corner of the camera on the map.
    size : Size
        Size of the camera.

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

        Notes
        -----
        This is the exact algorithm used by `Widget.render_intersection`.
        """
        submap = np.zeros((self.size), dtype=np.uint8)

        mh, mw = map.shape
        h, w = self.size

        y, x = self.pos
        b, r = h + y, w + x

        if (
            y >= mh
            or b < 0
            or x >= mw
            or r < 0
        ):
            return submap

        if y < 0:
            st = -y
            dt = 0

            if b >= mh:
                sb = mh + st
                db = mh
            else:
                sb = h
                db = b
        else:
            st = 0
            dt = y

            if b >= mh:
                sb = mh - dt
                db = mh
            else:
                sb = h
                db = b

        if x < 0:
            sl = -x
            dl = 0

            if r >= mw:
                sr = mw + sl
                dr = mw
            else:
                sr = w
                dr = r
        else:
            sl = 0
            dl = x

            if r >= mw:
                sr = mw - dl
                dr = mw
            else:
                sr = w
                dr = r

        submap[st: sb, sl: sr] = map[dt: db, dl: dr]

        return submap


class Interval(NamedTuple):
    """
    A continuous interval.
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

    Notes
    -----
    This differs from `Point` as it expects arbitrary floats
    (as opposed to ints) for each coordinate.
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
        Intensity of light source. If a `Color` is given it will
        be converted to an intensity with `LightIntensity.from_color`.
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
    PERMISSIVE = "permissive"
    MODERATE = "moderate"
    RESTRICTIVE = "restrictive"
