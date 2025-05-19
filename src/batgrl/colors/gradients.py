"""Functions for blending colors and creating color gradients."""

from itertools import pairwise
from math import sin, tau

from ..geometry import lerp
from ..geometry.easings import EASINGS, Easing
from .color_types import AColor, Color

__all__ = ["darken_only", "gradient", "lerp_colors", "lighten_only", "rainbow_gradient"]


def darken_only(a: Color, b: Color) -> Color:
    """
    Return a color that is the minimum of each channel in ``a`` and ``b``.

    Parameters
    ----------
    a : Color
        A color.
    b : Color
        A color.

    Returns
    -------
    Color
        A color with smallest components of ``a`` and ``b``.
    """
    color = (min(c1, c2) for c1, c2 in zip(a, b))
    return Color(*color)


def lighten_only(a: Color, b: Color) -> Color:
    """
    Return a color that is the maximum of each channel in ``a`` and ``b``.

    Parameters
    ----------
    a : Color
        A color.
    b : Color
        A color.

    Returns
    -------
    Color
        A color with largest components of ``a`` and ``b``.
    """
    color = (max(c1, c2) for c1, c2 in zip(a, b))
    return Color(*color)


def lerp_colors[T: (Color, AColor, tuple[int, ...])](a: T, b: T, p: float) -> T:
    """
    Linear interpolation from ``a`` to ``b`` with proportion ``p``.

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
        The linear interpolation of ``a`` and ``b``.
    """
    color = (round(lerp(c1, c2, p)) for c1, c2 in zip(a, b))
    if isinstance(a, (Color, AColor)):
        return type(a)(*color)
    return tuple(color)  # type: ignore


def gradient[T: (Color, AColor, tuple[int, ...])](
    *color_stops: T, n: int, easing: Easing = "linear"
) -> list[T]:
    r"""
    Return a smooth gradient of length ``n`` between all colors in ``color_stops``.

    Parameters
    ----------
    \*color_stops : (Color, AColor, tuple[int, ...])
        Colors between each gradient.
    n : int
        Length of gradient. Must be equal to or larger than ``color_stops``.
    easing : Easing, default: "linear"
        Easing applied to interpolations between ``color stops``.

    Returns
    -------
    list[(Color, AColor, tuple[int, ...])]
        A smooth gradient between all colors in ``color_stops``.
    """
    ncolors = len(color_stops)
    if n < ncolors:
        raise ValueError(f"gradient too small to contain all color stops ({n=})")
    if ncolors == 1:
        return [color_stops[0]] * n

    ease = EASINGS[easing]
    d, r = divmod(n - ncolors, ncolors - 1)
    gradient: list[T] = []
    b = color_stops[0]
    for i, (a, b) in enumerate(pairwise(color_stops)):
        gradient.append(a)
        len_ = d + (i < r)
        gradient.extend(
            lerp_colors(a, b, ease((j + 1) / (len_ + 1))) for j in range(len_)
        )
    gradient.append(b)
    return gradient


def rainbow_gradient(n: int, *, alpha: int | None = None) -> list[Color] | list[AColor]:
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
    offsets: list[float] = [0, tau / 3, 2 * tau / 3]

    def color(i: int):
        return Color(*(int(sin(i * theta + offset) * 127 + 128) for offset in offsets))

    if alpha is None:
        return [color(i) for i in range(n)]

    return [AColor(*color(i), alpha) for i in range(n)]
