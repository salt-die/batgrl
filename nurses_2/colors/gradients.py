"""
Functions for creating color gradients.
"""
import numpy as np

from .color_types import RGB, ColorPair
from .colors import BLACK, WHITE

__all__ = (
    "fg_rainbow",
    "bg_rainbow",
    "gradient",
)

def _rainbow_gradient(n):
    """
    Return a rainbow gradient of `n` (r, g, b)-tuples.
    """
    TAU = 2 * np.pi
    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])
    THETA = TAU / n

    for i in range(n):
        yield RGB(
            *(np.sin(THETA * i + OFFSETS) * 127 + 128).astype(np.uint8)
        )

def fg_rainbow(n=20, bg_color=BLACK):
    """
    Return a rainbow gradient of `n` ColorPairs with a given background color.
    """
    for fg_color in _rainbow_gradient(n):
        yield ColorPair(*fg_color, *bg_color)

def bg_rainbow(n=20, fg_color=WHITE):
    """
    Return a rainbow gradient of `n` ColorPairs with a given foreground color.
    """
    for bg_color in _rainbow_gradient(n):
        yield ColorPair(*fg_color, *bg_color)

def lerp(start, end, percent):
    """
    Linear interpolation between `start` and `end`.
    """
    return round(percent * end + (1 - percent) * start)

def gradient(n, start_pair: ColorPair, end_pair: ColorPair):
    """
    Return a gradient from `start_pair` to `end_pair` with `n` (n > 1) colors.
    """
    yield start_pair

    for i in range(n - 2):
        percent = (i + 1) / (n - 1)
        yield ColorPair(*map(lerp, start_pair, end_pair, (percent,) * 6))

    yield end_pair
