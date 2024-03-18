"""An image painted with box unicode characters."""
from pathlib import Path

import cv2
import numpy as np

from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text
from .text_tools import binary_to_box

__all__ = ["BoxImage", "Point", "Size"]


class BoxImage(Gadget):
    r"""
    An image painted with box unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    alpha : float, default: 1.0
        Transparency of gadget.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    path : pathlib.Path
        Path to image.
    alpha : float
        Transparency of gadget.
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
    on_size()
        Update gadget after a resize.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root()
        Yield all descendents of the root gadget (preorder traversal).
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    on_key(key_event)
        Handle key press event.
    on_mouse(mouse_event)
        Handle mouse event.
    on_paste(paste_event)
        Handle paste event.
    tween(...)
        Sequentially update gadget properties over time.
    on_add()
        Apply size hints and call children's `on_add`.
    on_remove()
        Call children's `on_remove`.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        path: Path,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._image = Text()
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.add_gadget(self._image)
        self.path = path
        self.alpha = alpha

    @property
    def is_transparent(self) -> bool:
        """Whether gadget is transparent."""
        return self._image.is_transparent

    @is_transparent.setter
    def is_transparent(self, is_transparent: bool):
        self._image.is_transparent = is_transparent

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._image.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._image.alpha = alpha

    @property
    def path(self) -> Path | None:
        """Path to image."""
        return self._path

    @path.setter
    def path(self, path: Path | None):
        self._path: Path | None = path

        if path is None:
            self._otexture = np.zeros((1, 1, 3), dtype=np.uint8)
        else:
            self._otexture = cv2.imread(str(path.absolute()), cv2.IMREAD_COLOR)
        self._load_texture()

    def on_size(self):
        """Remake canvas."""
        self._image.size = self.size
        self._load_texture()

    def _load_texture(self):
        h, w = self.size
        if h == 0 or w == 0:
            return

        canvas = self._image.canvas
        img_bgr = cv2.resize(self._otexture, (2 * w, 2 * h))
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 2, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 2, w, 2, 3), 1, 2)

        # First, find the average lightness of each 2x2 section of the image
        # (`average_lightness`). Boxes are placed where the lightness is greater than
        # `average_lightness`. The background color will be the average of the colors
        # darker than `average_lightness`. The foreground color will be the average of
        # the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_boxes = lightness > average_lightness[..., None, None]

        canvas["char"] = binary_to_box(where_boxes)

        nboxes = where_boxes.sum(axis=(2, 3))
        nboxes_neg = 4 - nboxes
        nboxes[nboxes == 0] = 1
        nboxes_neg[nboxes_neg == 0] = 1

        foreground = rgb_sectioned.copy()
        foreground[~where_boxes] = 0
        canvas["fg_color"] = foreground.sum(axis=(2, 3)) / nboxes[..., None]

        background = rgb_sectioned.copy()
        background[where_boxes] = 0
        canvas["bg_color"] = background.sum(axis=(2, 3)) / nboxes_neg[..., None]
