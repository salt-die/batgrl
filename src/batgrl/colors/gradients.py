"""Functions for blending colors and creating color gradients."""

from math import sin, tau
from typing import cast

import numpy as np

from ..geometry import clamp, lerp, normalize
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
    color = (clamp(round(lerp(c1, c2, p)), 0, 255) for c1, c2 in zip(a, b))
    if isinstance(a, (Color, AColor)):
        return type(a)(*color)
    return cast(T, tuple(color))


def gradient[T: (Color, AColor, tuple[int, ...])](
    *colors: T, n: int, easing: Easing = "linear"
) -> list[T]:
    r"""
    Return a smooth gradient of length ``n`` between all colors in ``colors``.

    Parameters
    ----------
    \*colors : (Color, AColor, tuple[int, ...])
        Pairwise colors determine start and end of each subgradient.
    n : int
        Length of gradient. Must be equal to or larger than ``colors``.
    easing : Easing, default: "linear"
        Easing applied to entire gradient.

    Returns
    -------
    list[(Color, AColor, tuple[int, ...])]
        A smooth gradient between all colors in ``colors``.
    """
    ncolors = len(colors)
    if n < ncolors:
        raise ValueError(f"gradient too small to contain all colors ({n=})")
    if ncolors == 1:
        return [colors[0]] * n

    ease = EASINGS[easing]
    pcolors: list[float] = np.linspace(0.0, 1.0, ncolors).tolist()
    eased_pcolors = [ease(p) for p in pcolors]

    i = 1
    gradient: list[T] = []
    for p in np.linspace(0.0, 1.0, n).tolist():
        while p > pcolors[i]:
            i += 1
        gradient.append(
            lerp_colors(
                colors[i - 1],
                colors[i],
                normalize(ease(p), eased_pcolors[i - 1], eased_pcolors[i]),
            )
        )
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
