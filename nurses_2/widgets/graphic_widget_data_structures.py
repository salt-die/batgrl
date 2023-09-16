"""
Graphic widget data structures.
"""
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from ..data_structures import Point, Size
from .widget import Rect, intersection

__all__ = "Interpolation", "read_texture", "resize_texture", "composite"

Interpolation = Literal["nearest", "linear", "cubic", "area", "lanczos"]
"""Interpolation methods for resizing graphic widgets."""

Interpolation._to_cv_enum = {
    "linear": cv2.INTER_LINEAR,
    "cubic": cv2.INTER_CUBIC,
    "area": cv2.INTER_AREA,
    "lanczos": cv2.INTER_LANCZOS4,
    "nearest": cv2.INTER_NEAREST,
}


def read_texture(path: Path) -> NDArray[np.uint8]:
    """
    Return a uint8 RGBA numpy array from a path to an image.
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


def resize_texture(
    texture: NDArray[np.uint8], size: Size, interpolation: Interpolation = "linear"
) -> NDArray[np.uint8]:
    """
    Resize texture.
    """
    w, h = size
    return cv2.resize(
        texture,
        (w, h),
        interpolation=Interpolation._to_cv_enum[interpolation],
    )


def composite(
    source: NDArray[np.uint8],
    dest: NDArray[np.uint8],
    pos: Point = Point(0, 0),
    mask_mode: bool = False,
):
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

        dest_tex = dest[dest_slice]
        source_tex = source[source_slice]
        source_alpha = source_tex[..., 3]

        if mask_mode:
            mask = source_alpha == 255
            dest_tex[mask] = source_tex[mask]
        else:
            buffer = np.subtract(source_tex, dest_tex, dtype=float)
            buffer *= source_alpha[..., None]
            buffer /= 255
            np.add(buffer, dest_tex, out=dest_tex, casting="unsafe")
