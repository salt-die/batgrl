from ...colors import WHITE_ON_BLACK, ColorPair
from ._field_base import _FieldBase, _ParticleBase


class TextParticleField(_FieldBase):
    """
    A widget that only has `TextParticle` children.
    """
    def render(self, canvas_view, colors_view, rect):
        t, l, _, _, h, w = rect

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
                colors_view[pos] = child.default_color_pair


class TextParticle(_ParticleBase):
    """
    A 1x1 TUI element.
    """
    def __init__(
        self,
        *,
        char=" ",
        default_color_pair: ColorPair=WHITE_ON_BLACK,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.char = char
        self.default_color_pair = default_color_pair


TextParticleField._child_type = TextParticle
