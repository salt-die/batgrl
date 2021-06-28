"""
RGB and ColorPair types and some utility functions for colors live here.
"""
from typing import NamedTuple

import numpy as np

__all__ = (
    "RGB",
    "ColorPair",
    "fg_rainbow",
    "bg_rainbow",
    "gradient",
)

TAU = 2 * np.pi


class RGB(NamedTuple):
    """
    A tuple representing a 24-bit color.
    """
    r: int
    g: int
    b: int


WHITE = RGB(255, 255, 255)
BLACK = RGB(0, 0, 0)


class ColorPair(NamedTuple):
    """
    A tuple representing a foreground and background color.
    """
    fg_r: int
    fg_g: int
    fg_b: int
    bg_r: int
    bg_g: int
    bg_b: int


WHITE_ON_BLACK = ColorPair(*WHITE, *BLACK)


def _rainbow_gradient(n):
    """
    Return a rainbow gradient of `n` (r, g, b)-tuples.
    """

    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])

    for i in range(n):
        THETA = TAU / n * i
        yield RGB(
            *(np.sin(THETA + OFFSETS) * 127 + 128).astype(int)
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
