"""Functions for blending colors and creating color gradients."""

from math import sin, tau

from ..geometry import lerp
from .color_types import AColor, Color

__all__ = ["darken_only", "lighten_only", "lerp_colors", "gradient", "rainbow_gradient"]


def darken_only(a: Color, b: Color) -> Color:
    """
    Return a color that is the minimum of each channel in `a` and `b`.

    Parameters
    ----------
    a : Color
        A color.
    b : Color
        A color.

    Returns
    -------
    Color
        A color with smallest components of `a` and `b`.
    """
    color = (min(c1, c2) for c1, c2 in zip(a, b))
    return Color(*color)


def lighten_only(a: Color, b: Color) -> Color:
    """
    Return a color that is the maximum of each channel in `a` and `b`.

    Parameters
    ----------
    a : Color
        A color.
    b : Color
        A color.

    Returns
    -------
    Color
        A color with largest components of `a` and `b`.
    """
    color = (max(c1, c2) for c1, c2 in zip(a, b))
    return Color(*color)


def lerp_colors[T: (Color, AColor, tuple[int, ...])](a: T, b: T, p: float) -> T:
    """
    Linear interpolation from `a` to `b` with proportion `p`.

    Parameters
    ----------
    a : (Color, AColor, tuple[int, ...])
        A color.
    b : (Color, AColor, tuple[int, ...])
        A color.
    p : float
        Proportion from a to b.

    Returns
    -------
    (Color, AColor, tuple[int, ...])
        The linear interpolation of `a` and `b`.
    """
    color = (round(lerp(c1, c2, p)) for c1, c2 in zip(a, b))
    if isinstance(a, (Color, AColor)):
        return type(a)(*color)
    return tuple(color)


def gradient[T: (Color, AColor, tuple[int, ...])](
    start: T, end: T, ncolors: int
) -> list[T]:
    """
    Return a gradient from `start` to `end` with `ncolors` (> 1) colors.

    Parameters
    ----------
    start : (Color, AColor, tuple[int, ...])
        Start color of gradient.
    end : (Color, AColor, tuple[int, ...])
        End color of gradient.
    ncolors : int
        Number of colors in gradient.

    Returns
    -------
    list[(Color, AColor, tuple[int, ...])]
        A gradient of colors from `start` to `end`.
    """
    if ncolors < 2:
        raise ValueError(f"not enough colors ({ncolors=})")

    return [lerp_colors(start, end, i / (ncolors - 1)) for i in range(ncolors)]


def rainbow_gradient(n: int, *, alpha: int | None = None) -> list[Color | AColor]:
    """
    Return a rainbow gradient of ``n`` colors.

    Parameters
    ----------
    n : int
        Number of colors in gradient.
    alpha : int | None, default: None
        If ``alpha`` is not given, gradient colors will have no alpha channel.
        Otherwise, the color's alpha channel is given by ``alpha``.

    Returns
    -------
    list[Color | AColor]
        A rainbow gradient of colors.
    """
    theta = tau / n
    offsets = [0, tau / 3, 2 * tau / 3]

    def color(i):
        return (int(sin(i * theta + offset) * 127 + 128) for offset in offsets)

    if alpha is None:
        return [Color(*color(i)) for i in range(n)]

    return [AColor(*color(i), alpha) for i in range(n)]
