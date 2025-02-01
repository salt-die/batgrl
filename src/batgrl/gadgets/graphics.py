"""A graphic gadget."""

from pathlib import Path
from typing import Final, Literal

import cv2
import numpy as np
from numpy.typing import NDArray

from .._rendering import graphics_render
from ..colors import TRANSPARENT, AColor
from ..texture_tools import Interpolation, resize_texture
from .gadget import Cell, Gadget, Point, PosHint, Size, SizeHint, bindable, clamp

__all__ = ["Blitter", "Graphics", "Interpolation", "Point", "Size", "scale_geometry"]

Blitter = Literal["braille", "full", "half", "sixel"]
"""Determines how graphics are rendered."""

_BLITTER_GEOMETRY: Final[dict[Blitter, Size]] = {
    "braille": Size(4, 2),
    "full": Size(1, 1),
    "half": Size(2, 1),
    "sixel": Size(20, 10),
}


def scale_geometry[T: (Point, Size)](blitter: Blitter, point_or_size: T) -> T:
    """
    Scale a point or size by some blitter geometry.

    Parameters
    ----------
    blitter : Blitter
        Blitter from which pixel geometry is chosen.
    point_or_size : T
        A point or size to scale.

    Returns
    -------
    T
        The scaled geometry.
    """
    h, w = _BLITTER_GEOMETRY[blitter]
    a, b = point_or_size
    if blitter == "sixel":
        ah, _ = Graphics._sixel_aspect_ratio
        return type(point_or_size)(h * a // ah, w * b)
    return type(point_or_size)(h * a, w * b)


class Graphics(Gadget):
    r"""
    A graphic gadget. Displays arbitrary RGBA textures.

    Graphic gadgets' color information is stored in a uint8 RGBA array, :attr:`texture`.
    The size of :attr:`texture` depends on the geometry of the chosen blitter. For
    instance, if the chosen blitter is "half", then the texture will be twice the height
    of the gadget and the same width.

    Parameters
    ----------
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

    _sixel_support: bool = False
    """Whether sixel is supported."""
    _sixel_aspect_ratio: Size = Size(1, 1)
    """Sixel aspect ratio."""

    def __init__(
        self,
        *,
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
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.default_color = default_color
        self.alpha = alpha
        self.interpolation = interpolation
        self.texture = np.full((1, 1, 4), default_color, np.uint8)
        self.blitter = blitter  # Property setter will correctly resize texture.

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    @bindable
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    @property
    def interpolation(self) -> Interpolation:
        """Interpolation used when gadget is resized."""
        return self._interpolation

    @interpolation.setter
    def interpolation(self, interpolation: Interpolation):
        if interpolation not in Interpolation.__args__:
            raise TypeError(f"{interpolation} is not a valid interpolation type.")
        self._interpolation = interpolation

    @property
    def blitter(self) -> Blitter:
        """Determines how graphics are rendered."""
        return self._blitter

    @blitter.setter
    def blitter(self, blitter: Blitter):
        if blitter not in Blitter.__args__:
            raise TypeError(f"{blitter} is not a valid blitter type.")
        if blitter == "sixel" and not self._sixel_support:
            self._blitter = "half"
        else:
            self._blitter = blitter
        self.on_size()

    def on_size(self) -> None:
        """Resize texture array."""
        self.texture = resize_texture(
            self.texture, scale_geometry(self._blitter, self.size), self._interpolation
        )

    def on_add(self) -> None:
        """Resize if geometry is incorrect on add."""
        if self._blitter == "sixel" and not Graphics._sixel_support:
            self.blitter = "half"
        elif self.texture.shape[:2] != scale_geometry(self._blitter, self.size):
            self.on_size()
        super().on_add()

    def to_png(self, path: Path) -> None:
        """Write :attr:`texture` to provided path as a `png` image."""
        BGRA = cv2.cvtColor(self.texture, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path.absolute()), BGRA)

    def clear(self) -> None:
        """Fill texture with default color."""
        self.texture[:] = self.default_color

    def _render(
        self, cells: NDArray[Cell], graphics: NDArray[np.uint8], kind: NDArray[np.uint8]
    ) -> None:
        """Render visible region of gadget."""
        graphics_render(
            cells,
            graphics,
            kind,
            self.absolute_pos,
            self._blitter,
            self._is_transparent,
            self.texture,
            self._alpha,
            self._region,
        )
