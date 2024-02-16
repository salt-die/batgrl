"""Functions for creating color gradients."""
import numpy as np

from ..geometry import lerp
from .color_types import AColor, Color

__all__ = ["gradient", "lerp_colors", "rainbow_gradient"]

AnyColor = Color | AColor


def rainbow_gradient(n: int, *, color_type: type[AnyColor] = Color) -> list[AnyColor]:
    """
    Return a rainbow gradient of `n` colors.

    Parameters
    ----------
    n : int
        Number of colors in gradient.
    color_type : AnyColor, default: Color
        Color type of gradient.

    Returns
    -------
    list[AnyColor]
        A rainbow gradient of colors.
    """
    TAU = 2 * np.pi
    OFFSETS = np.array([0, TAU / 3, 2 * TAU / 3])
    THETA = TAU / n

    return [
        color_type(*(int(j) for j in (np.sin(THETA * i + OFFSETS) * 127 + 128)))
        for i in range(n)
    ]


def lerp_colors(start: AnyColor, end: AnyColor, p: float) -> AnyColor:
    """
    Linear interpolation from `start` to `end` with proportion `p`.

    Parameters
    ----------
    start : AnyColor
        Start color.
    end : AnyColor
        End Color
    p : float
        Proportion from start to end.

    Returns
    -------
    AnyColor
        The linear interpolation of `start` and `end`.
    """
    return type(start)(*(round(lerp(a, b, p)) for a, b in zip(start, end)))


def gradient(start: AnyColor, end: AnyColor, ncolors: int) -> list[AnyColor]:
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.

    Parameters
    ----------
    start : AnyColor
        Start color or colorpair.
    end : AnyColor
        End color of colorpair.
    ncolors : int
        Number of colors in gradient.

    Returns
    -------
    list[AnyColor]
        A gradient of colors from `start` to `end`.
    """
    if ncolors < 2:
        raise ValueError(f"not enough colors ({ncolors=})")

    return [lerp_colors(start, end, i / (ncolors - 1)) for i in range(ncolors)]
