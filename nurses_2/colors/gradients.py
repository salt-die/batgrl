"""
Functions for creating color gradients.
"""
import numpy as np

from .color_types import RGB, ColorPair
from .colors import BLACK, WHITE

__all__ = (
    "foreground_rainbow",
    "background_rainbow",
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

def foreground_rainbow(ncolors=20, background_color=BLACK):
    """
    A rainbow gradient of `ncolors` ColorPairs with a given background color.
    """
    return [
        ColorPair(*foreground_color, *background_color)
        for foreground_color in _rainbow_gradient(ncolors)
    ]

def background_rainbow(ncolors=20, foreground_color=WHITE):
    """
    Return a rainbow gradient of `ncolors` ColorPairs with a given foreground color.
    """
    return [
        ColorPair(*foreground_color, *background_color)
        for background_color in _rainbow_gradient(ncolors)
    ]

def lerp(start_pair: ColorPair, end_pair: ColorPair, percent):
    """
    Linear interpolation between `start_pair` and `end_pair`.
    """
    for a, b in zip(start_pair, end_pair):
        yield round((1 - percent) * a + percent * b)

def gradient(ncolors, start_pair: ColorPair, end_pair: ColorPair):
    """
    Return a gradient from `start_pair` to `end_pair` with `ncolors` (> 1) colors.
    """
    assert ncolors > 1, f"not enough colors ({ncolors=})"

    grad = [ start_pair ]

    for i in range(ncolors - 2):
        percent = (i + 1) / (ncolors - 1)
        grad.append(
            ColorPair(*lerp(start_pair, end_pair, percent))
        )

    grad.append(end_pair)

    return grad
