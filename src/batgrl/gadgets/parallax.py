"""A parallax gadget."""

from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Self

import numpy as np
from numpy.typing import NDArray

from ..colors import TRANSPARENT, AColor
from ..texture_tools import composite, read_texture, resize_texture
from .graphics import (
    Blitter,
    Graphics,
    Interpolation,
    Point,
    PosHint,
    Size,
    SizeHint,
    scale_geometry,
)

__all__ = ["Parallax", "Interpolation", "Point", "Size"]


class Parallax(Graphics):
    r"""
    A parallax gadget.

    Parameters
    ----------
    path : Path | None, default: None
        Path to directory of images for layers of the parallax (loaded in lexographical
        order of filenames) layered from background to foreground.
    speeds : Sequence[float] | None, default: None
        The scrolling speed of each layer. Default speeds are `1/(N - i)` where `N` is
        the number of layers and `i` is the index of a layer.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        Transparency of gadget.
    interpolation : Interpolation, default: "linear"
        Interpolation used when gadget is resized.
    blitter : Blitter, default: "half"
        Determines how graphics are rendered.
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
    layers : list[Image]
        Layers of the parallax.
    speeds : Sequence[float]
        The scrolling speed of each layer.
    offset : tuple[float, float]
        Vertical and horizontal offset of the parallax.
    vertical_offset : float
        Vertical offset of the parallax.
    horizontal_offset : float
        Horizontal offset of the parallax.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget.
    interpolation : Interpolation
        Interpolation used when gadget is resized.
    blitter : Blitter
        Determines how graphics are rendered.
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
    to_png(path)
        Write :attr:`texture` to provided path as a `png` image.
    clear()
        Fill texture with default color.
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
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        blitter: Blitter = "half",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self.layers: list[NDArray[np.uint8]]
        """Layers of the parallax."""

        if path is None:
            self.layers = []
        else:
            paths = sorted(path.iterdir(), key=lambda file: file.name)
            self.layers = [read_texture(path) for path in paths]

        self.speeds: Sequence[float]
        """The scrolling speed of each layer."""

        nlayers = len(self.layers)
        if speeds is None:
            self.speeds = [1 / (nlayers - i) for i in range(nlayers)]
        elif nlayers != len(speeds):
            raise ValueError("number of layers doesn't match number of layer speeds")
        else:
            self.speeds = speeds

        self._vertical_offset = self._horizontal_offset = 0.0

        super().__init__(
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            blitter=blitter,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    def on_size(self):
        """Resize parallax layers."""
        h, w = scale_geometry(self._blitter, self._size)
        self.texture = np.empty((h, w, 4), np.uint8)
        self._sized_layers = [
            resize_texture(texture, (h, w), self.interpolation)
            for texture in self.layers
        ]
        self._update_texture()

    @property
    def vertical_offset(self) -> float:
        """Vertical offset of the parallax."""
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset: float):
        self._vertical_offset = offset
        self._update_texture()

    @property
    def horizontal_offset(self) -> float:
        """Horizontal offset of the parallax."""
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset: float):
        self._horizontal_offset = offset
        self._update_texture()

    @property
    def offset(self) -> tuple[float, float]:
        """Vertical and horizontal offset of the parallax."""
        return self._vertical_offset, self._horizontal_offset

    @offset.setter
    def offset(self, offset: tuple[float, float]):
        self._vertical_offset, self._horizontal_offset = offset
        self._update_texture()

    def _update_texture(self):
        self.clear()
        for speed, texture in zip(self.speeds, self._sized_layers):
            rolls = (
                -round(speed * self._vertical_offset),
                -round(speed * self._horizontal_offset),
            )
            composite(np.roll(texture, rolls, axis=(0, 1)), self.texture)

    @classmethod
    def from_textures(
        cls,
        textures: Iterable[NDArray[np.uint8]],
        *,
        speeds: Sequence[float] | None = None,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        blitter: Blitter = "half",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = True,
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
        default_color : AColor, default: AColor(0, 0, 0, 0)
            Default texture color.
        alpha : float, default: 1.0
            Transparency of gadget.
        interpolation : Interpolation, default: "linear"
            Interpolation used when gadget is resized.
        blitter : Blitter, default: "half"
            Determines how graphics are rendered.
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
        layers = list(textures)
        nlayers = len(layers)
        if speeds is None:
            speeds = [1 / (nlayers - i) for i in range(nlayers)]
        elif nlayers != len(speeds):
            raise ValueError("number of layers doesn't match number of layer speeds")

        parallax = cls(
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            blitter=blitter,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        parallax.layers = layers
        parallax.speeds = speeds
        parallax.on_size()
        return parallax
