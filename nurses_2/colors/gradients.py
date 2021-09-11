"""
Functions for creating color gradients.
"""
import numpy as np

from .color_data_structures import *
from .colors import BLACK, WHITE, color_pair

__all__ = (
    "rainbow_gradient",
    "foreground_rainbow",
    "background_rainbow",
    "gradient",
)

def rainbow_gradient(n):
    """
    Return a rainbow gradient of `n` `Color`s.
    """
    TAU = 2 * np.pi
    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])
    THETA = TAU / n

    for i in range(n):
        yield Color(
            *(np.sin(THETA * i + OFFSETS) * 127 + 128).astype(np.uint8)
        )

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

def lerp(start, end, proportion):
    """
    Linear interpolation between `start` and `end`.
    """
    for a, b in zip(start, end):
        yield round((1 - proportion) * a + proportion * b)

def gradient(start, end, ncolors):
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.
    """
    assert ncolors > 1, f"not enough colors ({ncolors=})"

    grad = [ start ]

    for i in range(ncolors - 2):
        proportion = (i + 1) / (ncolors - 1)
        grad.append(
            tuple(lerp(start, end, proportion))
        )

    grad.append(end)

    return grad
