import numpy as np

from .particle_field import ParticleField, Particle
from ..colors import BLACK


class HalfBlockField(ParticleField):
    """
    A widget that only has HalfBlockParticle children.

    Notes
    -----
    HalfBlockFields are an optimized way to render many .5x1 TUI elements.

    Raises
    ------
    TypeError if `add_widget` argument is not an instance of `HalfBlockParticle`.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.buffer = np.zeros((3, ), dtype=np.float16)

    def add_widget(self, widget):
        if not isinstance(widget, HalfBlockParticle):
            raise TypeError(f"expected HalfBlockParticle, got {type(widget).__name__}")

        super().add_widget(widget)

    def render(self, canvas_view, colors_view, rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        buffer = self.buffer
        subtract, multiply, add = np.subtract, np.multiply, np.add
        t, l, _, _, h, w = rect

        for child in self.children:
            ct = child.top
            pos = top, left = int(ct) - t, child.left - l

            if 0 <= top < h and 0 <= left < w:
                canvas_view[pos] = "▀"

                color = colors_view[pos][3:] if (ct % 1) >= .5 else colors_view[pos][:3]
                subtract(child.color, color, out=buffer, dtype=np.float16)
                multiply(buffer, child.alpha, out=buffer)
                add(buffer, color, out=color, casting="unsafe")


class HalfBlockParticle(Particle):
    """
    A .5x1 TUI element that's Widget-like, except it has no render method.

    Requires a `HalfBlockField` to be rendered.

    Notes
    -----
    The y-component of `pos` can be a float. The fractional part determines
    whether the half block is upper or lower.
    """
    def __init__(self, pos=(0, 0), *, color=BLACK, alpha=1.0):
        self.top, self.left = pos
        self.color = color
        self.alpha = alpha
        self.parent = None
