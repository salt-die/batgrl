import numpy as np

from ...colors import AColor, TRANSPARENT
from ._field_base import _ParticleFieldBase, _ParticleBase


class GraphicParticleField(_ParticleFieldBase):
    """
    A widget that only has GraphicParticle children.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._buffer = np.zeros((3, ), dtype=float)

    def render(self, canvas_view, colors_view, source_slice: tuple[slice, slice]):
        buffer = self._buffer
        subtract, add = np.subtract, np.add

        vert_slice, hori_slice = source_slice
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

    Notes
    -----
    The y-component of `pos` can be a float. The fractional part determines
    whether the half block is upper or lower.
    """
    def __init__(self, *, color: AColor=TRANSPARENT, is_transparent=True, **kwargs):
        super().__init__(is_transparent=is_transparent, **kwargs)

        self.color = color


GraphicParticleField._child_type = GraphicParticle
