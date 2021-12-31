from ...colors import WHITE_ON_BLACK, ColorPair
from ._field_base import _ParticleFieldBase, _ParticleBase


class TextParticleField(_ParticleFieldBase):
    """
    A widget that only has `TextParticle` children.
    """
    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        vert_slice, hori_slice = source
        t = vert_slice.start
        h = vert_slice.stop - t
        l = hori_slice.start
        w = hori_slice.stop - l

        for child in self.children:
            pos = top, left = child.top - t, child.left - l

            if (
                child.is_enabled
                and child.is_visible
                and not (child.is_transparent and child.char == " ")
                and 0 <= top < h
                and 0 <= left < w
            ):
                canvas_view[pos] = child.char
                colors_view[pos] = child.color_pair


class TextParticle(_ParticleBase):
    """
    A 1x1 TUI element.
    """
    def __init__(
        self,
        *,
        char=" ",
        color_pair: ColorPair=WHITE_ON_BLACK,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.char = char
        self.color_pair = color_pair


TextParticleField._child_type = TextParticle
