"""
Graphic widget data structures.
"""
from enum import IntEnum

import cv2

__all__ = "Interpolation",


class Interpolation(IntEnum):
    """
    Interpolation methods for resizing graphic widgets.

    :class:`Interpolation` is one of `NEAREST`, `LINEAR`, `CUBIC`, `AREA`,
    `LANCZOS`.
    """
    NEAREST = cv2.INTER_NEAREST
    LINEAR = cv2.INTER_LINEAR
    CUBIC = cv2.INTER_CUBIC
    AREA = cv2.INTER_AREA
    LANCZOS = cv2.INTER_LANCZOS4
