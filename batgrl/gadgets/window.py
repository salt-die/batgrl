"""
A movable, resizable window gadget.
"""
import numpy as np
from wcwidth import wcswidth

from ..colors import TRANSPARENT, AColor, ColorPair
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.resizable import Resizable
from .behaviors.themable import Themable
from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
)
from .graphics import Graphics, Interpolation
from .text import Text

__all__ = [
    "Interpolation",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Window",
]


class _TitleBar(Grabbable, Gadget):
    def __init__(self):
        super().__init__(pos=(1, 2), disable_ptf=True, background_char=" ")

        self._label = Text(pos_hint={"x_hint": 0.5, "anchor": "top"})
        self.add_gadget(self._label)

    def on_add(self):
        super().on_add()

        def update_size():
            self.size = 1, self.parent.width - 4

        update_size()
        self.subscribe(self.parent, "size", update_size)

    def on_remove(self):
        self.unsubscribe(self.parent, "size")
        super().on_remove()

    def grab_update(self, mouse_event):
        self.parent.top += self.mouse_dy
        self.parent.left += self.mouse_dx


class Window(Themable, Focusable, Resizable, Graphics):
    """
    A movable, resizable window gadget.

    The view can be set with the :attr:`view` property, e.g.,
    ``my_window.view = some_gadget``. Added views will have their size hints and
    visibility reset. Views are resized as the window is resized.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    resize_min_height : int | None, default: None
        Minimum height gadget can be resized by grabbing. Minimum height can't be less
        than 3.
    resize_min_width : int | None, default: None
        Minimum width gadget can be resized by grabbing. Minimum width can't be less
        than 6 + column width of title.
    border_alpha : float, default: 1.0
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor, default: TRANSPARENT
        Color of border.
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
    view : Gadget
        The windowed gadget.
    title : str
        Title of window.
    is_focused : bool
        True if gadget has focus.
    any_focused : bool
        True if any gadget has focus.
    allow_vertical_resize : bool
        Allow vertical resize.
    allow_horizontal_resize : bool
        Allow horizontal resize.
    resize_min_height : int
        Minimum height gadget can be resized by grabbing.
    resize_min_width : int
        Minimum width gadget can be resized by grabbing.
    border_alpha : float
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor
        Color of border.
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
    update_theme:
        Paint the gadget with current theme.
    focus:
        Focus gadget.
    blur:
        Un-focus gadget.
    focus_next:
        Focus next focusable gadget.
    focus_previous:
        Focus previous focusable gadget.
    on_focus:
        Called when gadget is focused.
    on_blur:
        Called when gadget loses focus.
    pull_border_to_front:
        Pull borders to the front.
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
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

    Notes
    -----
    If not given or too small, :attr:`resize_min_height` and
    :attr:`resize_min_width` will be set large enough so that the border and title
    are visible.
    """

    def __init__(
        self,
        *,
        title="",
        allow_vertical_resize: bool = True,
        allow_horizontal_resize: bool = True,
        resize_min_height: int | None = None,
        resize_min_width: int | None = None,
        border_alpha: float = 1.0,
        border_color: AColor = TRANSPARENT,
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self._title = title

        super().__init__(
            allow_vertical_resize=allow_vertical_resize,
            allow_horizontal_resize=allow_horizontal_resize,
            resize_min_height=resize_min_height,
            resize_min_width=resize_min_width,
            border_alpha=border_alpha,
            border_color=border_color,
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self._view = None
        self._titlebar = _TitleBar()
        self.add_gadget(self._titlebar)
        self.title = title

    @property
    def resize_min_height(self) -> int:
        return self._resize_min_height

    @resize_min_height.setter
    def resize_min_height(self, min_height: int | None):
        if min_height is None:
            self._resize_min_height = 3
        else:
            self._resize_min_height = clamp(min_height, 3, None)

    @property
    def resize_min_width(self) -> int:
        return self._resize_min_width

    @resize_min_width.setter
    def resize_min_width(self, min_width: int | None):
        w = 6 + wcswidth(self._title)
        if min_width is None:
            self._resize_min_width = w
        else:
            self._resize_min_width = clamp(min_width, w, None)

    @property
    def view(self) -> Gadget | None:
        """
        The windowed gadget.
        """
        return self._view

    @view.setter
    def view(self, view: Gadget | None):
        if self._view is not None:
            self.remove_gadget(self._view)

        self._view = view

        if view is not None:
            view.pos = 2, 2
            view.size_hint.height_hint = None
            view.size_hint.width_hint = None
            self.add_gadget(view)
            self.pull_border_to_front()
            self.on_size()

    def on_size(self):
        h, w = self._size
        self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)
        self.texture[4:-2, 2:-2] = self.default_color

        if self._view is not None:
            self._view.size = h - 3, w - 4

        self._view.is_visible = h - 3 > 0 and w - 4 > 0

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.width = wcswidth(title)
        self._titlebar._label.add_str(title)
        self.resize_min_width = self.resize_min_width

    def update_theme(self):
        self.default_color = AColor(*self.color_theme.primary.bg_color)
        self.texture[4:-2, 2:-2] = self.default_color

        if self.is_focused:
            title_color = self.color_theme.titlebar_normal
            self._titlebar.background_color_pair = title_color
            self._titlebar._label.default_color_pair = title_color
            self._titlebar._label.colors[:] = title_color

            self.border_color = self.color_theme.window_border_normal
        else:
            title_color = self.color_theme.titlebar_inactive
            self._titlebar.background_color_pair = title_color
            self._titlebar._label.default_color_pair = title_color
            self._titlebar._label.colors[:] = title_color

            self.border_color = self.color_theme.window_border_inactive

    def on_focus(self):
        self.update_theme()
        self.pull_to_front()

    def on_blur(self):
        self.update_theme()

    def dispatch_mouse(self, mouse_event):
        return super().dispatch_mouse(mouse_event) or self.collides_point(
            mouse_event.position
        )
