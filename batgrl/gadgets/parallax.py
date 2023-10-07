"""
A parallax gadget.
"""
from collections.abc import Iterable, Sequence
from numbers import Real
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from ..colors import ColorPair
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Region,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
    subscribable,
)
from .image import Image, Interpolation

__all__ = [
    "Interpolation",
    "Parallax",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


def _check_layer_speeds(
    layers: Sequence[Image], speeds: Sequence[Real] | None
) -> Sequence[Real]:
    """
    Raise `ValueError` if `layers` and `speeds` are incompatible, else return a sequence
    of layer speeds.
    """
    nlayers = len(layers)
    if speeds is None:
        return [1 / (nlayers - i) for i in range(nlayers)]

    if len(speeds) != nlayers:
        raise ValueError("number of layers doesn't match number of layer speeds")

    return speeds


class Parallax(Gadget):
    """
    A parallax gadget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for layers of the parallax (loaded
        in lexographical order of filenames) layered from background to foreground.
    speeds : Sequence[Real] | None, default: None
        The scrolling speed of each layer. Default speeds are `1/(N - i)`
        where `N` is the number of layers and `i` is the index of a layer.
    alpha : float, default: 1.0
        Transparency of the parallax.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    offset : tuple[float, float]
        Vertical and horizontal offset of first layer of the parallax. Other layers will
        be adjusted automatically.
    layers : list[Image]
        Layers of the parallax.
    speeds : Sequence[Real]
        The scrolling speed of each layer.
    vertical_offset : float
        Vertical offset of first layer of the parallax.
    horizontal_offset : float
        Horizontal offset of first layer of the parallax
    alpha : float
        Transparency of the parallax.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    size : Size
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    from_textures:
        Create a :class:`Parallax` from an iterable of uint8 RGBA numpy array.
    from_images:
        Create a :class:`Parallax` from an iterable of :class:`Image`.
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        path: Path | None = None,
        speeds: Sequence[Real] | None = None,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        is_transparent: bool = True,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self.layers: list[Image]
        """Layers of the parallax."""

        if path is None:
            self.layers = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.layers = [Image(path=path) for path in paths]
            for layer in self.layers:
                layer.parent = self

        super().__init__(
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.speeds = _check_layer_speeds(self.layers, speeds)
        self.alpha = alpha
        self.interpolation = interpolation

        self._vertical_offset = self._horizontal_offset = 0.0

    @property
    def region(self) -> Region:
        return self._region

    @region.setter
    def region(self, region: Region):
        self._region = region
        for layer in self.layers:
            layer.region = region

    def on_size(self):
        for layer in self.layers:
            layer.size = self._size
        self._otextures = [layer.texture for layer in self.layers]

    @property
    def is_transparent(self) -> bool:
        """
        If false, `alpha` and alpha channels are ignored.
        """
        return self._is_transparent

    @is_transparent.setter
    def is_transparent(self, transparent: bool):
        self._is_transparent = transparent
        for layer in self.layers:
            layer.is_transparent = True

    @property
    def alpha(self) -> float:
        """
        Transparency of gadget if :attr:`is_transparent` is true.
        """
        return self._alpha

    @alpha.setter
    @subscribable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)
        for layer in self.layers:
            layer.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        """
        Interpolation used when gadget is resized.
        """
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        if interpolation not in {"nearest", "linear", "cubic", "area", "lanczos"}:
            raise ValueError(f"{interpolation} is not a valid interpolation type.")
        for layer in self.layers:
            layer.interpolation = interpolation

    @property
    def vertical_offset(self) -> float:
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset: float):
        self._vertical_offset = offset
        self._adjust()

    @property
    def horizontal_offset(self) -> float:
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset: float):
        self._horizontal_offset = offset
        self._adjust()

    @property
    def offset(self) -> tuple[float, float]:
        return self._vertical_offset, self._horizontal_offset

    @offset.setter
    def offset(self, offset: tuple[float, float]):
        self._vertical_offset, self._horizontal_offset = offset
        self._adjust()

    def _adjust(self):
        for speed, texture, layer in zip(
            self.speeds,
            self._otextures,
            self.layers,
        ):
            rolls = -round(speed * self._vertical_offset), -round(
                speed * self._horizontal_offset
            )
            layer.texture = np.roll(texture, rolls, axis=(0, 1))

    def render(self, canvas: NDArray[Char], colors: NDArray[np.uint8]):
        if self.layers:
            for layer in self.layers:
                layer.render(canvas, colors)
        else:
            super().render(canvas, colors)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[NDArray[np.uint8]],
        *,
        speeds: Sequence[float] | None = None,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        is_transparent: bool = True,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ) -> "Parallax":
        """
        Create an :class:`Parallax` from an iterable of uint8 RGBA numpy array.
        """
        parallax = cls(
            speeds=speeds,
            alpha=alpha,
            interpolation=interpolation,
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )
        parallax.layers = [
            Image.from_texture(
                texture,
                size=parallax.size,
                alpha=parallax.alpha,
                interpolation=parallax.interpolation,
            )
            for texture in textures
        ]
        for layer in parallax.layers:
            layer.parent = parallax
        parallax.speeds = _check_layer_speeds(parallax.layers, speeds)
        return parallax

    @classmethod
    def from_images(
        cls,
        images: Iterable[Image],
        *,
        speeds: Sequence[float] | None = None,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        is_transparent: bool = True,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ) -> "Parallax":
        """
        Create an :class:`Parallax` from an iterable of :class:`Image`.
        """
        parallax = cls(
            alpha=alpha,
            interpolation=interpolation,
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )
        parallax.layers = list(images)
        for image in parallax.layers:
            image.interpolation = parallax.interpolation
            image.size = parallax.size
            image.alpha = parallax.alpha
            image.parent = parallax
        parallax.speeds = _check_layer_speeds(parallax.layers, speeds)
        return parallax
