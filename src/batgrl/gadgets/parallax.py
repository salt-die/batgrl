"""A parallax gadget."""

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Self

import numpy as np
from numpy.typing import NDArray

from .gadget import (
    Cell,
    Gadget,
    Point,
    PosHint,
    Region,
    Size,
    SizeHint,
    bindable,
    clamp,
)
from .image import Image, Interpolation

__all__ = ["Parallax", "Interpolation", "Point", "Size"]


def _check_layer_speeds(
    layers: Sequence[Image], speeds: Sequence[float] | None
) -> Sequence[float]:
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
    r"""
    A parallax gadget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for layers of the parallax (loaded
        in lexographical order of filenames) layered from background to foreground.
    speeds : Sequence[float] | None, default: None
        The scrolling speed of each layer. Default speeds are `1/(N - i)` where `N` is
        the number of layers and `i` is the index of a layer.
    alpha : float, default: 1.0
        Transparency of gadget.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: True
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    offset : tuple[float, float]
        Vertical and horizontal offset of first layer of the parallax.
    layers : list[Image]
        Layers of the parallax.
    speeds : Sequence[float]
        The scrolling speed of each layer.
    vertical_offset : float
        Vertical offset of first layer of the parallax.
    horizontal_offset : float
        Horizontal offset of first layer of the parallax.
    alpha : float
        Transparency of gadget.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    from_textures(textures, ...)
        Create a :class:`Parallax` from an iterable of uint8 RGBA numpy array.
    from_images(images, ...)
        Create a :class:`Parallax` from an iterable of :class:`Image`.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    def __init__(
        self,
        *,
        path: Path | None = None,
        speeds: Sequence[float] | None = None,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        is_transparent: bool = True,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.layers: list[Image]
        """Layers of the parallax."""

        if path is None:
            self.layers = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.layers = [Image(path=path, is_transparent=True) for path in paths]
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
        )

        self.speeds = _check_layer_speeds(self.layers, speeds)
        self.alpha = alpha
        self.interpolation = interpolation
        self._vertical_offset = self._horizontal_offset = 0.0
        self.on_size()

    @property
    def _region(self) -> Region:
        """The visible portion of the gadget on the screen."""
        return self._region_value

    @_region.setter
    def _region(self, region: Region):
        self._region_value = region
        for layer in self.layers:
            layer._region = region

    def on_size(self):
        """Resize parallax layers."""
        for layer in self.layers:
            layer.size = self._size
        self._otextures = [layer.texture for layer in self.layers]

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    @bindable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)
        for layer in self.layers:
            layer.alpha = alpha

    @property
    def interpolation(self) -> Interpolation:
        """Interpolation used when gadget is resized."""
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        if interpolation not in {"nearest", "linear", "cubic", "area", "lanczos"}:
            raise ValueError(f"{interpolation} is not a valid interpolation type.")
        for layer in self.layers:
            layer.interpolation = interpolation

    @property
    def vertical_offset(self) -> float:
        """Vertical offset of first layer of the parallax."""
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset: float):
        self._vertical_offset = offset
        self._adjust()

    @property
    def horizontal_offset(self) -> float:
        """Horizontal offset of first layer of the parallax."""
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset: float):
        self._horizontal_offset = offset
        self._adjust()

    @property
    def offset(self) -> tuple[float, float]:
        """
        Vertical and horizontal offset of first layer of the parallax.

        Other layers will be adjusted automatically when offset is set.
        """
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
            rolls = (
                -round(speed * self._vertical_offset),
                -round(speed * self._horizontal_offset),
            )
            layer.texture = np.roll(texture, rolls, axis=(0, 1))

    def _render(self, canvas: NDArray[Cell]):
        """Render visible region of gadget."""
        if self.layers:
            for layer in self.layers:
                layer._render(canvas)
        else:
            super()._render(canvas)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[NDArray[np.uint8]],
        *,
        speeds: Sequence[float] | None = None,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        is_transparent: bool = True,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> Self:
        """
        Create an :class:`Parallax` from an iterable of uint8 RGBA numpy array.

        Parameters
        ----------
        textures : Iterable[NDArray[np.uint8]]
            An iterable of RGBA textures that will be the layers of the parallax.
        speeds : Sequence[float] | None, default: None
            The scrolling speed of each layer. Default speeds are `1/(N - i)` where `N`
            is the number of layers and `i` is the index of a layer.
        alpha : float, default: 1.0
            Transparency of gadget.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        size : Size, default: Size(10, 10)
            Size of gadget.
        pos : Point, default: Point(0, 0)
            Position of upper-left corner in parent.
        size_hint : SizeHint | None, default: None
            Size as a proportion of parent's height and width.
        pos_hint : PosHint | None, default: None
            Position as a proportion of parent's height and width.
        is_transparent : bool, default: True
            Whether gadget is transparent.
        is_visible : bool, default: True
            Whether gadget is visible. Gadget will still receive input events if not
            visible.
        is_enabled : bool, default: True
            Whether gadget is enabled. A disabled gadget is not painted and doesn't
            receive input events.

        Returns
        -------
        Parallax
            A new parallax gadget.
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
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> Self:
        """
        Create an :class:`Parallax` from an iterable of :class:`Image`.

        Parameters
        ----------
        textures : Iterable[Image]
            An iterable of images that will be the layers of the parallax.
        speeds : Sequence[float] | None, default: None
            The scrolling speed of each layer. Default speeds are `1/(N - i)` where `N`
            is the number of layers and `i` is the index of a layer.
        alpha : float, default: 1.0
            Transparency of gadget.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        size : Size, default: Size(10, 10)
            Size of gadget.
        pos : Point, default: Point(0, 0)
            Position of upper-left corner in parent.
        size_hint : SizeHint | None, default: None
            Size as a proportion of parent's height and width.
        pos_hint : PosHint | None, default: None
            Position as a proportion of parent's height and width.
        is_transparent : bool, default: True
            Whether gadget is transparent.
        is_visible : bool, default: True
            Whether gadget is visible. Gadget will still receive input events if not
            visible.
        is_enabled : bool, default: True
            Whether gadget is enabled. A disabled gadget is not painted and doesn't
            receive input events.

        Returns
        -------
        Parallax
            A new parallax gadget.
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
        )
        parallax.layers = list(images)
        for image in parallax.layers:
            image.interpolation = parallax.interpolation
            image.size = parallax.size
            image.alpha = parallax.alpha
            image.parent = parallax
        parallax.speeds = _check_layer_speeds(parallax.layers, speeds)
        return parallax
