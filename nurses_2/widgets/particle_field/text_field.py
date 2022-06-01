"""
A text particle field. A particle field specializes in handling many
single "pixel" children.
"""
from ...colors import WHITE_ON_BLACK, ColorPair
from ._field_base import _ParticleFieldBase, _ParticleBase


class TextParticleField(_ParticleFieldBase):
    """
    A widget that only has `TextParticle` children.

    Raises
    ------
    TypeError
        If `add_widget` is called with a non-`TextParticle`.
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
    char : str, default: " ",
        A one-character string.
    color_pair: ColorPair, default: WHITE_ON_BLACK
        Color pair of the particle.

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
    char : str
        A one-character string.
    color_pair : ColorPair
        Color pair of particle.
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
