"""A graphic gadget."""

from pathlib import Path

import cv2
import numpy as np
from numpy.typing import NDArray

from ..colors import TRANSPARENT, AColor
from ..geometry import rect_slice
from ..text_tools import cell_sans
from ..texture_tools import Interpolation, _composite, resize_texture
from .gadget import Cell, Gadget, Point, PosHint, Size, SizeHint, bindable, clamp

__all__ = ["Graphics", "Interpolation", "Point", "Size"]


class Graphics(Gadget):
    r"""
    A graphic gadget. Displays arbitrary RGBA textures.

    Graphic gadgets are gadgets that are rendered entirely with the upper half block
    character, "▀". Graphic gadgets' color information is stored in a uint8 RGBA array,
    :attr:`texture`. Note that the height of :attr:`texture` is twice the height of the
    gadget.

    Parameters
    ----------
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
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
    texture : NDArray[np.uint8]
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
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
        is_transparent: bool = True,
        default_color: AColor = TRANSPARENT,
        alpha: float = 1.0,
        interpolation: Interpolation = "linear",
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_transparent=is_transparent,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.default_color = default_color
        self.alpha = alpha
        self.interpolation = interpolation

        h, w = self.size
        self.texture = np.full((2 * h, w, 4), default_color, dtype=np.uint8)

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

    def on_size(self):
        """Resize texture array."""
        h, w = self.size
        self.texture = resize_texture(self.texture, (2 * h, w), self.interpolation)

    def _render(self, canvas: NDArray[Cell]):
        """Render visible region of gadget."""
        texture = self.texture
        chars = canvas["char"]
        styles = canvas[cell_sans("char", "fg_color", "bg_color")]
        foreground = canvas["fg_color"]
        background = canvas["bg_color"]
        root_pos = self.root._pos
        abs_pos = self.absolute_pos
        alpha = self.alpha
        for pos, (h, w) in self._region.rects():
            dst = rect_slice(pos - root_pos, (h, w))
            src_top, src_left = pos - abs_pos
            src_bottom, src_right = src_top + h, src_left + w
            fg_rect = foreground[dst]
            bg_rect = background[dst]
            even_rows = texture[2 * src_top : 2 * src_bottom : 2, src_left:src_right]
            odd_rows = texture[2 * src_top + 1 : 2 * src_bottom : 2, src_left:src_right]

            if self.is_transparent:
                mask = chars[dst] != "▀"
                fg_rect[mask] = bg_rect[mask]
                _composite(fg_rect, even_rows[..., :3], even_rows[..., 3, None], alpha)
                _composite(bg_rect, odd_rows[..., :3], odd_rows[..., 3, None], alpha)
            else:
                fg_rect[:] = even_rows[..., :3]
                bg_rect[:] = odd_rows[..., :3]

            chars[dst] = "▀"
            styles[dst] = False

    def to_png(self, path: Path):
        """Write :attr:`texture` to provided path as a `png` image."""
        BGRA = cv2.cvtColor(self.texture, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path.absolute()), BGRA)

    def clear(self):
        """Fill texture with default color."""
        self.texture[:] = self.default_color
