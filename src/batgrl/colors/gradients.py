"""Functions for blending colors and creating color gradients."""
from math import sin, tau

from ..geometry import lerp
from .color_types import Color

__all__ = ["darken_only", "lighten_only", "lerp_colors", "gradient", "rainbow_gradient"]


def darken_only(a: tuple, b: tuple) -> tuple:
    """
    Return a color that is the minimum of each channel in `a` and `b`.

    Parameters
    ----------
    a : tuple
        A color.
    b : tuple
        A color.

    Returns
    -------
    tuple
        A color with smallest components of `a` and `b`.
    """
    color = (min(c1, c2) for c1, c2 in zip(a, b))
    if hasattr(a, "_fields"):  # NamedTuple
        return type(a)(*color)
    return tuple(color)


def lighten_only(a: tuple, b: tuple) -> tuple:
    """
    Return a color that is the maximum of each channel in `a` and `b`.

    Parameters
    ----------
    a : tuple
        A color.
    b : tuple
        A color.

    Returns
    -------
    tuple
        A color with largest components of `a` and `b`.
    """
    color = (max(c1, c2) for c1, c2 in zip(a, b))
    if hasattr(a, "_fields"):  # NamedTuple
        return type(a)(*color)
    return tuple(color)


def lerp_colors(a: tuple, b: tuple, p: float) -> tuple:
    """
    Linear interpolation from `a` to `b` with proportion `p`.

    If `a` is a named tuple the return type will be the same type.

    Parameters
    ----------
    a : tuple
        A color.
    b : tuple
        A color.
    p : float
        Proportion from a to b.

    Returns
    -------
    tuple
        The linear interpolation of `a` and `b`.
    """
    color = (round(lerp(c1, c2, p)) for c1, c2 in zip(a, b))
    if hasattr(a, "_fields"):  # NamedTuple
        return type(a)(*color)
    return tuple(color)


def gradient(start: tuple, end: tuple, ncolors: int) -> list[tuple]:
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.

    Parameters
    ----------
    start : tuple
        Start color of gradient.
    end : tuple
        End color of gradient.
    ncolors : int
        Number of colors in gradient.

    Returns
    -------
    list[tuple]
        A gradient of colors from `start` to `end`.
    """
    if ncolors < 2:
        raise ValueError(f"not enough colors ({ncolors=})")

    return [lerp_colors(start, end, i / (ncolors - 1)) for i in range(ncolors)]


def rainbow_gradient(n: int, *, color_type: type[tuple] = Color) -> list[tuple]:
    """
    Return a rainbow gradient of `n` colors.

    Parameters
    ----------
    n : int
        Number of colors in gradient.
    color_type : tuple, default: Color
        Color type of gradient.

    Returns
    -------
    list[tuple]
        A rainbow gradient of colors.
    """
    theta = tau / n
    offsets = [0, tau / 3, 2 * tau / 3]

    def color(i):
        return (int(sin(i * theta + offset) * 127 + 128) for offset in offsets)

    if hasattr(color_type, "_fields"):
        return [color_type(*color(i)) for i in range(n)]
    return [color_type(color(i)) for i in range(n)]
