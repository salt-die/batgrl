"""
Graphic widget data structures.
"""
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from ..data_structures import *
from ..clamp import clamp
from .widget import intersection, Rect

__all__ = "Interpolation", "Sprite"


class Interpolation(str, Enum):
    """
    Interpolation methods for resizing graphic widgets.

    :class:`Interpolation` is one of `NEAREST`, `LINEAR`, `CUBIC`, `AREA`,
    `LANCZOS`.
    """
    NEAREST = "nearest"
    LINEAR = "linear"
    CUBIC = "cubic"
    AREA = "area"
    LANCZOS = "lanczos"


Interpolation._to_cv_enum = {
    Interpolation.LINEAR: cv2.INTER_LINEAR,
    Interpolation.CUBIC: cv2.INTER_CUBIC,
    Interpolation.AREA: cv2.INTER_AREA,
    Interpolation.LANCZOS: cv2.INTER_LANCZOS4,
    Interpolation.NEAREST: cv2.INTER_NEAREST,
}


class Sprite:
    """
    A graphic element.

    :class:`Sprite` simplifies reading images and painting and compositing textures.

    Parameters
    ----------
    texture : numpy.ndarray
        uint8 RGBA color array.
    alpha : float, default: 1.0
        The alpha channel of :attr:`texture` will be multiplied by this
        when compositing with :meth:`paint`.

    Attributes
    ----------
    texture : numpy.ndarray
        uint8 RGBA color array.
    alpha : float
        The alpha channel of :attr:`texture` will be multiplied by this
        when compositing with :meth:`paint`.

    Methods
    -------
    resize:
        Return a new sprite with given size.
    paint:
        Compose sprite with another texture.
    from_image:
        Create a sprite from an image.
    read_image:
        Create a uint8 rgba texture from an image.
    """
    def __init__(self, texture: np.ndarray, alpha: float=1.0):
        self.texture = texture
        self.alpha = alpha

    @property
    def size(self) -> Size:
        """
        Size of sprite.
        """
        return Size(*self.texture.shape[:2])

    def resize(self, size: Size, interpolation: Interpolation=Interpolation.LINEAR) -> "Sprite":
        """
        Return a new sprite with resized :attr:`texture`.
        """
        h, w = size
        h = clamp(h, 1, None)
        w = clamp(w, 1, None)

        return Sprite(
            cv2.resize(
                self.texture,
                (w, h),
                interpolation=Interpolation._to_cv_enum[interpolation],
            ),
            self.alpha,
        )

    @property
    def alpha(self) -> float:
        """
        Transparency of sprite.
        """
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    def paint(self, texture: np.ndarray, pos: Point=Point(0, 0)):
        """
        Paint this sprite on the given texture at position `pos`.
        """
        th, tw, _ = texture.shape
        dest = Rect(0, th, 0, tw)

        top, left = pos
        h, w = self.size
        bottom, right = top + h, left + w
        source = Rect(top, bottom, left, right)

        if (slices := intersection(dest, source)) is not None:
            dest_slice, source_slice = slices

            dest_tex = texture[dest_slice][..., :3]
            source_tex = self.texture[source_slice]

            buffer = np.subtract(source_tex[..., :3], dest_tex, dtype=float)
            buffer *= source_tex[..., 3, None]
            buffer *= self.alpha / 255

            np.add(buffer, dest_tex, out=dest_tex, casting="unsafe")

    @classmethod
    def from_image(cls, path: Path) -> "Sprite":
        """
        Create a :class:`Sprite` from an image.
        """
        return cls(cls.read_image(path))

    @staticmethod
    def read_image(path: Path) -> np.ndarray:
        """
        Create a `numpy.ndarray` from an image.
        """
        image = cv2.imread(str(path.absolute()), cv2.IMREAD_UNCHANGED)

        if image.dtype == np.dtype(np.uint16):
            image = (image // 257).astype(np.uint8)
        elif image.dtype == np.dtype(np.float32):
            image = (image * 255).astype(np.uint8)

        # Add an alpha channel if there isn't one.
        h, w, c = image.shape
        if c == 3:
            default_alpha_channel = np.full((h, w, 1), 255, dtype=np.uint8)
            image = np.dstack((image, default_alpha_channel))

        return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)
