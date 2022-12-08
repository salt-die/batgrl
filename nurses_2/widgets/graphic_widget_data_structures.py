"""
Graphic widget data structures.
"""
from enum import Enum
from pathlib import Path

import cv2
import numpy as np

from ..data_structures import *
from .widget import intersection, Rect

__all__ = "Interpolation", "read_texture", "resize_texture", "composite"


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

def read_texture(path: Path) -> np.ndarray:
    """
    Return a uint8 RBGA np.ndarray from a path to an image.
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

def resize_texture(texture: np.ndarray, size: Size, interpolation: Interpolation=Interpolation.LINEAR) -> np.ndarray:
    """
    Resize texture.
    """
    w, h = size
    return cv2.resize(
        texture,
        (w, h),
        interpolation=Interpolation._to_cv_enum[interpolation],
    )

def composite(source: np.ndarray, dest: np.ndarray, pos: Point=Point(0, 0), mask_mode: bool=False):
    """
    Composite source texture onto destination texture at given position.

    If `mask_mode` is true, source alpha values less than 255 are ignored.
    """
    sh, sw, _ = source.shape
    dh, dw, _ = dest.shape
    y, x = pos

    source_rect = Rect(y, y + sh, x, x + sw)
    dest_rect = Rect(0, dh, 0, dw)

    if (slices := intersection(source_rect, dest_rect)) is not None:
        source_slice, dest_slice = slices

        dest_tex = dest[dest_slice][..., :3]
        source_tex = source[source_slice]

        if mask_mode:
            mask = source_tex[..., 3] == 255
            dest_tex[mask] = source_tex[..., :3][mask]
        else:
            buffer = np.subtract(source_tex[..., :3], dest_tex, dtype=float)
            buffer *= source_tex[..., 3, None]
            buffer /= 255

            np.add(buffer, dest_tex, out=dest_tex, casting="unsafe")
