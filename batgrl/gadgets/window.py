"""A movable, resizable window gadget."""
import numpy as np
from wcwidth import wcswidth

from ..colors import TRANSPARENT, AColor
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
from .gadget_base import GadgetBase
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
        super().__init__(
            pos=(1, 2),
            size=(1, 2),
            disable_ptf=True,
            background_char=" ",
            size_hint={"width_hint": 1.0, "width_offset": -4},
        )

        self._label = Text(pos_hint={"x_hint": 0.5, "anchor": "top"})
        self.add_gadget(self._label)

    def grab_update(self, mouse_event):
        self.parent.top += self.mouse_dy
        self.parent.left += self.mouse_dx


class Window(Themable, Focusable, Resizable, Graphics):
    r"""
    A movable, resizable window gadget.

    The view can be set with the :attr:`view` property, e.g.,
    ``my_window.view = some_gadget``.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    resize_min_height : int | None, default: None
        Minimum height gadget can be resized by grabbing.
    resize_min_width : int | None, default: None
        Minimum width gadget can be resized by grabbing.
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
    view : GadgetBase
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
    update_theme():
        Paint the gadget with current theme.
    focus():
        Focus gadget.
    blur():
        Un-focus gadget.
    focus_next():
        Focus next focusable gadget.
    focus_previous():
        Focus previous focusable gadget.
    on_focus():
        Update gadget when it gains focus.
    on_blur():
        Update gadget when it loses focus.
    pull_border_to_front():
        Pull borders to the front.
    to_png(path):
        Write :attr:`texture` to provided path as a `png` image.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
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
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.

    Notes
    -----
    Windows remove size and pos hints from their children.

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
        )

        self._view = None
        self._titlebar = _TitleBar()
        self.add_gadget(self._titlebar)
        self.title = title

    @property
    def resize_min_height(self) -> int:
        """Minimum height gadget can be resized by grabbing."""
        return self._resize_min_height

    @resize_min_height.setter
    def resize_min_height(self, min_height: int | None):
        if min_height is None:
            self._resize_min_height = 3
        else:
            self._resize_min_height = clamp(min_height, 3, None)

    @property
    def resize_min_width(self) -> int:
        """Minimum width gadget can be resized by grabbing."""
        return self._resize_min_width

    @resize_min_width.setter
    def resize_min_width(self, min_width: int | None):
        w = 6 + wcswidth(self._title)
        if min_width is None:
            self._resize_min_width = w
        else:
            self._resize_min_width = clamp(min_width, w, None)

    @property
    def view(self) -> GadgetBase | None:
        """The windowed gadget."""
        return self._view

    @view.setter
    def view(self, view: GadgetBase | None):
        if self._view is not None:
            self.remove_gadget(self._view)

        self._view = view

        if view is not None:
            view.size_hint = {}
            view.pos_hint = {}
            view.pos = 2, 2
            self.add_gadget(view)
            self.pull_border_to_front()
            self.on_size()

    def on_size(self):
        """Resize view on resize."""
        h, w = self._size
        self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)
        self.texture[4:-2, 2:-2] = self.default_color

        if self._view is not None:
            self._view.size = h - 3, w - 4
            self._view.is_visible = h - 3 > 0 and w - 4 > 0

    @property
    def title(self):
        """Title of window."""
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.width = wcswidth(title)
        self._titlebar._label.add_str(title)
        self.resize_min_width = self.resize_min_width

    def update_theme(self):
        """Paint the gadget with current theme."""
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
        """Pull window to front and recolor borders on focus."""
        self.update_theme()
        self.pull_to_front()

    def on_blur(self):
        """Recolor borders on blur."""
        self.update_theme()

    def dispatch_mouse(self, mouse_event):
        """Handle any colliding mouse events."""
        return super().dispatch_mouse(mouse_event) or self.collides_point(
            mouse_event.position
        )
