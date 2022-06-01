"""
A graphic particle field. A particle field specializes in handling many
single "pixel" children.
"""
import numpy as np

from ...colors import AColor, ABLACK
from ._field_base import _ParticleFieldBase, _ParticleBase


class GraphicParticleField(_ParticleFieldBase):
    """
    A widget that only has `GraphicParticle` children.

    Raises
    ------
    TypeError
        If `add_widget` is called with a non-`GraphicParticle`.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._buffer = np.zeros((3, ), dtype=float)

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        buffer = self._buffer
        subtract, add = np.subtract, np.add

        vert_slice, hori_slice = source
        t = vert_slice.start
        h = vert_slice.stop - t
        l = hori_slice.start
        w = hori_slice.stop - l

        for child in self.children:
            if not child.is_enabled or not child.is_visible:
                continue

            ct = child.top
            pos = top, left = int(ct) - t, child.left - l

            if 0 <= top < h and 0 <= left < w:
                canvas_view[pos] = "▀"

                *rgb, a = child.color
                if child.is_transparent:
                    color = colors_view[pos][np.s_[3:] if (ct % 1) >= .5 else np.s_[:3]]
                    subtract(rgb, color, out=buffer, dtype=float)
                    buffer *= a / 255
                    add(buffer, color, out=color, casting="unsafe")
                else:
                    colors_view[pos][np.s_[3:] if (ct % 1) >= .5 else np.s_[:3]] = rgb


class GraphicParticle(_ParticleBase):
    """
    A .5x1 TUI element.

    Parameters
    ----------
    pos : Point, default: Point(0, 0)
        Position of particle.
    is_transparent : bool, default: False
        If true, particle is transparent.
    is_visible : bool, default: True
        If true, particle is visible.
    is_enabled : bool, default: True
        If true, particle is enabled.
    color : AColor, default: ABLACK
        Color of particle.

    Attributes
    ----------
    pos : Point
        Position of particle.
    is_transparent : bool
        If true, particle is transparent.
    is_visible : bool
        If true, particle is visible.
    is_enabled : bool
        If true, particle is enabled.
    color : AColor
        Color of particle.
    size : Size
        Size of particle. Always `Size(1, 1)`.
    top : int
        Y-coordinate of particle.
    left : int
        X-coordinate of particle.
    height : Literal[1]
        Height of particle.
    width : Literal[1]
        Width of particle
    bottom : int
        `top` + 1
    right : int
        `left` + 1

    Methods
    -------
    to_local
        Convert absolute coordinates to relative coordinates.
    on_press
        Handle key press event.
    on_click
        Handle mouse event.
    on_double_click
        Handle double-click mouse event.
    on_triple-click
        Handle triple-click mouse event.
    on_paste
        Handle paste event.

    Notes
    -----
    The y-component of `pos` can be a float. The fractional part determines
    whether the half block is upper or lower.
    """
    def __init__(self, *, color: AColor=ABLACK, is_transparent=True, **kwargs):
        super().__init__(is_transparent=is_transparent, **kwargs)

        self.color = color


GraphicParticleField._child_type = GraphicParticle
