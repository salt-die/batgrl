"""An image painted with braille unicode characters."""

from pathlib import Path

import cv2
import numpy as np

from ..text_tools import binary_to_braille
from ..texture_tools import Interpolation, resize_texture
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .text import Text

__all__ = ["BrailleImage", "Interpolation", "Point", "Size"]


class BrailleImage(Gadget):
    r"""
    An image painted with braille unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
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
        path: Path,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._image = Text(is_transparent=is_transparent)
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
        self.alpha = alpha
        self.interpolation = interpolation
        self.path = path

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._image.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._image.alpha = alpha

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

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._image.is_transparent = self.is_transparent

    def on_size(self):
        """Resize canvas and colors arrays."""
        self._image.size = self.size
        self._load_texture()

    def _load_texture(self):
        h, w = self.size
        if h == 0 or w == 0:
            return

        canvas = self._image.canvas
        img_bgr = resize_texture(self._otexture, (4 * h, 2 * w), self.interpolation)
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 4, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 4, w, 2, 3), 1, 2)

        # First, find the average lightness of each 2x2 section of the image
        # (`average_lightness`). Boxes are placed where the lightness is greater than
        # `average_lightness`. The background color will be the average of the colors
        # darker than `average_lightness`. The foreground color will be the average of
        # the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_dots = lightness > average_lightness[..., None, None]

        canvas["char"] = binary_to_braille(where_dots)

        ndots = where_dots.sum(axis=(2, 3))
        ndots_neg = 8 - ndots
        ndots[ndots == 0] = 1
        ndots_neg[ndots_neg == 0] = 1

        foreground = rgb_sectioned.copy()
        foreground[~where_dots] = 0
        canvas["fg_color"] = foreground.sum(axis=(2, 3)) / ndots[..., None]

        background = rgb_sectioned.copy()
        background[where_dots] = 0
        canvas["bg_color"] = background.sum(axis=(2, 3)) / ndots_neg[..., None]
