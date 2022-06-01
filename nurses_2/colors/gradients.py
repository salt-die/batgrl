"""
Functions for creating color gradients.
"""
import numpy as np

from ..easings import lerp
from .color_data_structures import *
from .colors import BLACK, WHITE, ColorPair

__all__ = (
    "rainbow_gradient",
    "foreground_rainbow",
    "background_rainbow",
    "lerp_colors",
    "gradient",
)

def rainbow_gradient(n: int, *, color_type: Color | AColor=Color):
    """
    Return a rainbow gradient of ``n`` colors.

    Parameters
    ----------
    n : int
        Number of colors in gradient.
    color_type : Color | AColor, default: Color
        Type of color gradient to make
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

def foreground_rainbow(ncolors: int=20, bg_color: Color=BLACK):
    """
    A rainbow gradient of `ncolors` `ColorPair`s with a given background color.

    Parameters
    ----------
    ncolors : int, default: 20
        Number of colors in gradient.
    bg_color : Color, default: BLACK
        Background color used for gradient.
    """
    return [
        ColorPair.from_colors(fg_color, bg_color)
        for fg_color in rainbow_gradient(ncolors)
    ]

def background_rainbow(ncolors: int=20, fg_color: Color=WHITE):
    """
    Return a rainbow gradient of `ncolors` `ColorPair`s with a given foreground color.

    Parameters
    ----------
    ncolors : int, default: 20
        Number of colors in gradient.
    fg_color : Color, default: BLACK
        Foreground color used for gradient.
    """
    return [
        ColorPair.from_colors(fg_color, bg_color)
        for bg_color in rainbow_gradient(ncolors)
    ]

def lerp_colors(
    start: Color | AColor,
    end: Color | AColor,
    p: float
) -> Color | AColor:
    """
    Linear interpolation from `start` to `end` with proportion `p`.

    Parameters
    ----------
    start : Color | AColor
        Start color.
    end : Color | AColor
        End Color
    p : float
        Proportion from start to end.
    """
    return type(start)(
        *(round(lerp(a, b, p)) for a, b in zip(start, end))
    )

def gradient(
    start: Color | AColor | ColorPair,
    end: Color | AColor | ColorPair,
    ncolors: int
) -> list[Color | AColor | ColorPair]:
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.

    Parameters
    ----------
    start : Color | AColor | ColorPair
        Start color or colorpair.
    end : Color | AColor | ColorPair
        End color of colorpair.
    ncolors : int
        Number of colors in gradient.
    """
    if ncolors < 2:
        raise ValueError(f"not enough colors ({ncolors=})")

    return [lerp_colors(start, end, i / (ncolors - 1)) for i in range(ncolors)]
