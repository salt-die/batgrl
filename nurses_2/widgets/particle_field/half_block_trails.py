from collections import deque

import numpy as np

from ...colors import BLACK
from ...data_structures import Point
from ..widget_data_structures import Rect
from .particle_field import ParticleField, Particle

__all__ = "HalfBlockTrails", "TrailParticle"


class HalfBlockTrails(ParticleField):
    """
    A HalfBlockField that also renders trails to particles.

    Notes
    -----
    HalfBlockFields are an optimized way to render many .5x1 TUI elements.

    Raises
    ------
    TypeError if `add_widget` argument is not an instance of `HalfBlockParticle`.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._buffer = np.zeros((3, ), dtype=np.float16)

    def add_widget(self, widget):
        if not isinstance(widget, TrailParticle):
            raise TypeError(f"expected HalfBlockParticle, got {type(widget).__name__}")

        super().add_widget(widget)

    def render(self, canvas_view, colors_view, rect: Rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        buffer = self._buffer
        subtract, multiply, add = np.subtract, np.multiply, np.add
        t, l, _, _, h, w = rect

        for child in self.children:
            child.trail.appendleft(child.pos)
            child_color = child.color

            for (top, left), alpha in zip(child.trail, child.alphas):
                pos = offset_top, offset_left = int(top) - t, left - l

                if 0 <= offset_top < h and 0 <= offset_left < w:
                    canvas_view[pos] = "▀"

                    color = colors_view[pos][3:] if (top % 1) >= .5 else colors_view[pos][:3]
                    subtract(child_color, color, out=buffer, dtype=np.float16)
                    multiply(buffer, alpha, out=buffer)
                    add(buffer, color, out=color, casting="unsafe")


class TrailParticle(Particle):
    """
    A .5x1 TUI element that's Widget-like, except it has no render method.

    Requires a `HalfBlockField` to be rendered.

    Notes
    -----
    The y-component of `pos` can be a float. The fractional part determines
    whether the half block is upper or lower.
    """
    def __init__(self, pos=Point(0, 0), *, trail_length=3, color=BLACK, alpha=1.0, is_visible=True):
        self.top, self.left = pos
        self.color = color
        self.alpha = alpha
        self.is_visible = is_visible
        self.parent = None

        self.trail = deque(maxlen=trail_length + 1)
        self.alphas = np.linspace(1, 0, trail_length + 1, endpoint=False)
