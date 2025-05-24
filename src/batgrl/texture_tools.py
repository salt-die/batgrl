"""Tools for graphics."""

from pathlib import Path
from typing import Literal

import cv2
import numpy as np

from .array_types import RGBA_2D
from .geometry import Point, Region, Sizelike, rect_slice

__all__ = ["Interpolation", "composite", "read_texture", "resize_texture"]

Interpolation = Literal["nearest", "linear", "cubic", "area", "lanczos"]
"""Interpolation methods for resizing graphic gadgets."""

_INTERPOLATION_TO_CV_ENUM = {
    "linear": cv2.INTER_LINEAR,
    "cubic": cv2.INTER_CUBIC,
    "area": cv2.INTER_AREA,
    "lanczos": cv2.INTER_LANCZOS4,
    "nearest": cv2.INTER_NEAREST,
}


def read_texture(path: Path) -> RGBA_2D:
    """
    Return a uint8 RGBA numpy array from a path to an image.

    Parameters
    ----------
    path : Path
        Path to image.

    Returns
    -------
    RGBA_2D
        An uint8 RGBA array of the image.
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

    return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)  # type: ignore


def resize_texture(
    texture: RGBA_2D,
    size: Sizelike,
    interpolation: Interpolation = "linear",
    out: RGBA_2D | None = None,
) -> RGBA_2D:
    """
    Resize texture.

    Parameters
    ----------
    texture : RGBA_2D
        An RGBA texture to resize.
    size : Sizelike
        The new size of the texture.
    interpolation : Interpolation, default: "linear"
        Interpolation used when resizing texture.
    out : RGBA_2D | None, default: None
        Optional output array. If None, a new array is created.

    Returns
    -------
    RGBA_2D
        A new uint8 RGBA array.
    """
    old_h, old_w = texture.shape[:2]
    h, w = size
    if old_h == 0 or old_w == 0 or h == 0 or w == 0:
        return np.zeros((h, w, 4), np.uint8)
    return cv2.resize(
        texture, (w, h), dst=out, interpolation=_INTERPOLATION_TO_CV_ENUM[interpolation]
    )  # type: ignore


def composite(
    source: RGBA_2D,
    dest: RGBA_2D,
    pos: Point = Point(0, 0),
    mask_mode: bool = False,
) -> None:
    """
    Composite source texture onto destination texture at given position.

    If `mask_mode` is true, source alpha values less than 255 are ignored.

    Parameters
    ----------
    source : RGBA_2D
        The texture to composite.
    dest : RGBA_2D
        The texture on which the source is painted.
    pos : Pointlike, default: Point(0, 0)
        Position of the source on the destination.
    mask_mode : bool, default: False
        Whether to ignore alpha values less than 255.
    """
    sh, sw, _ = source.shape
    dh, dw, _ = dest.shape

    dest_reg = Region.from_rect((0, 0), (dh, dw))
    source_reg = Region.from_rect(pos, (sh, sw))

    if intersection := source_reg & dest_reg:
        rpos, size = next(intersection.rects())
        dest_tex = dest[rect_slice(rpos, size)]
        source_tex = source[rect_slice(rpos - pos, size)]
        source_alpha = source_tex[..., 3]

        if mask_mode:
            mask = source_alpha == 255
            dest_tex[mask] = source_tex[mask]
        else:
            buffer = np.subtract(source_tex, dest_tex, dtype=float)
            buffer *= source_alpha[..., None]
            buffer /= 255
            np.add(buffer, dest_tex, out=dest_tex, casting="unsafe")
