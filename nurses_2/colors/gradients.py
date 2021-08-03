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

def foreground_rainbow(ncolors=20, background: Color=BLACK):
    """
    A rainbow gradient of `ncolors` `color_pair`s with a given background color.
    """
    return [
        color_pair(foreground, background)
        for foreground in rainbow_gradient(ncolors)
    ]

def background_rainbow(ncolors=20, foreground: Color=WHITE):
    """
    Return a rainbow gradient of `ncolors` `color_pair`s with a given foreground color.
    """
    return [
        color_pair(foreground, background)
        for background in rainbow_gradient(ncolors)
    ]

def lerp(start_pair: ColorPair, end_pair: ColorPair, proportion):
    """
    Linear interpolation between `start_pair` and `end_pair`.
    """
    for a, b in zip(start_pair, end_pair):
        yield round((1 - proportion) * a + proportion * b)

def gradient(ncolors, start_pair: ColorPair, end_pair: ColorPair):
    """
    Return a gradient from `start_pair` to `end_pair` with `ncolors` (> 1) colors.
    """
    assert ncolors > 1, f"not enough colors ({ncolors=})"

    grad = [ start_pair ]

    for i in range(ncolors - 2):
        proportion = (i + 1) / (ncolors - 1)
        grad.append(
            ColorPair(*lerp(start_pair, end_pair, proportion))
        )

    grad.append(end_pair)

    return grad
