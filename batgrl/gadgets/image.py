"""
An image gadget.
"""
from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from ..colors import TRANSPARENT, AColor
from .graphics import (
    Graphics,
    Interpolation,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .texture_tools import read_texture

__all__ = [
    "Image",
    "Interpolation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class Image(Graphics):
    """
    An Image gadget.

    Parameters
    ----------
    path : pathlib.Path | None, default: None
        Path to image. If `None`, image will be :attr:`default_color`.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If gadget is transparent, the alpha channel of the underlying texture will be
        multiplied by this value. (0 <= alpha <= 1.0)
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
    is_transparent : bool, default: True
        A transparent gadget allows regions beneath it to be painted. Additionally,
        non-transparent graphic gadgets are not alpha composited.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    path : pathlib.Path | None
        Path to image if image was loaded from a path. Setting the path
        immediately reloads the image.
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of gadget if :attr:`is_transparent` is true.
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
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
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
    from_texture(texture, ...):
        Create an :class:`Image` from a uint8 RGBA numpy array.
    to_png(path):
        Write :attr:`texture` to provided path as a `png` image.
    on_size():
        Called when gadget is resized.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        True if point collides with visible portion of gadget.
    collides_gadget(other):
        True if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Called after a gadget is added to gadget tree.
    on_remove():
        Called before gadget is removed from gadget tree.
    prolicide():
        Recursively remove all children.
    destroy():
        Destroy this gadget and all descendents.
    """

    def __init__(
        self,
        *,
        path: Path | None = None,
        is_transparent: bool = True,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._otexture = np.zeros((2, 1, 4), dtype=np.uint8)
        super().__init__(
            is_transparent=is_transparent,
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.path = path

    @property
    def path(self) -> Path | None:
        return self._path

    @path.setter
    def path(self, new_path: Path | None):
        self._path = new_path
        if new_path is not None:
            self._otexture = read_texture(new_path)
        else:
            self._otexture = np.full((2, 1, 4), self.default_color, dtype=np.uint8)

        self.on_size()

    def on_size(self):
        h, w = self._size
        self.texture = cv2.resize(
            self._otexture,
            (w, 2 * h),
            interpolation=Interpolation._to_cv_enum[self.interpolation],
        )

    @classmethod
    def from_texture(
        cls,
        texture: NDArray[np.uint8],
        *,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = True,
        is_visible: bool = True,
        is_enabled: bool = True,
    ) -> "Image":
        """
        Create an :class:`Image` from a uint8 RGBA numpy array.

        Parameters
        ----------
        texture : NDArray[np.uint8]
            The RGBA texture of the image.
        default_color : AColor, default: AColor(0, 0, 0, 0)
            Default texture color.
        alpha : float, default: 1.0
            If gadget is transparent, the alpha channel of the underlying texture will
            be multiplied by this value. (0 <= alpha <= 1.0)
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
        is_transparent : bool, default: True
            If true, gadget is rendered with alpha compositing; otherwise, alpha values
            are ignored.
        is_visible : bool, default: True
            Whether gadget is visible. Gadget will still receive input events if not
            visible.
        is_enabled : bool, default: True
            Whether gadget is enabled. A disabled gadget is not painted and doesn't
            receive input events.

        Returns
        -------
        Image
            A new image gadget.
        """
        kls = cls(
            default_color=default_color,
            alpha=alpha,
            interpolation=interpolation,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        kls._otexture = texture
        kls.on_size()
        return kls
