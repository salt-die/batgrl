"""
Functions for creating color gradients.
"""
import numpy as np

from ..easings import lerp
from .color_data_structures import *
from .colors import BLACK, WHITE, color_pair

__all__ = (
    "rainbow_gradient",
    "foreground_rainbow",
    "background_rainbow",
    "gradient",
)

def rainbow_gradient(n, *, color_type=Color):
    """
    Return a rainbow gradient of `n` `Color`s.
    """
    TAU = 2 * np.pi
    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])
    THETA = TAU / n

    return [
        color_type(
            *(int(j) for j in (np.sin(THETA * i + OFFSETS) * 127 + 128))
        )
        for i in range(n)
    ]

def foreground_rainbow(ncolors=20, bg_color: Color=BLACK):
    """
    A rainbow gradient of `ncolors` `ColorPair`s with a given background color.
    """
    return [
        color_pair(fg_color, bg_color)
        for fg_color in rainbow_gradient(ncolors)
    ]

def background_rainbow(ncolors=20, fg_color: Color=WHITE):
    """
    Return a rainbow gradient of `ncolors` `ColorPair`s with a given foreground color.
    """
    return [
        color_pair(fg_color, bg_color)
        for bg_color in rainbow_gradient(ncolors)
    ]

def _lerp_color(start: Color | AColor, end: Color | AColor, p: float) -> Color | AColor:
    return type(start)(
        *(round(lerp(a, b, p)) for a, b in zip(start, end))
    )

def gradient(start: Color | AColor, end: Color | AColor, ncolors: int) -> list[Color | AColor]:
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.
    """
    if ncolors < 2:
        raise ValueError(f"not enough colors ({ncolors=})")

    return [_lerp_color(start, end, i / (ncolors - 1)) for i in range(ncolors)]
