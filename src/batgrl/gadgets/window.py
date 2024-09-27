"""A movable, resizable window gadget."""

from typing import Literal

from ..terminal.events import MouseEvent
from .behaviors.focusable import Focusable
from .behaviors.grabbable import Grabbable
from .behaviors.themable import Themable
from .gadget import Gadget, Point, PosHint, Size, SizeHint, clamp
from .pane import Pane
from .text import Text, str_width

__all__ = ["Window", "Point", "Size"]


class _TitleBar(Grabbable, Pane):
    def __init__(self):
        super().__init__(
            pos=(1, 2),
            size=(1, 2),
            size_hint={"width_hint": 1.0, "width_offset": -4},
            is_transparent=False,
        )

        self._label = Text(pos_hint={"x_hint": 0.5, "anchor": "top"})
        self.add_gadget(self._label)

    def grab_update(self, mouse_event):
        self.parent.top += mouse_event.dy
        self.parent.left += mouse_event.dx


class Window(Themable, Focusable, Grabbable, Gadget):
    r"""
    A movable, resizable window gadget.

    The view can be set with the :attr:`view` property, e.g.,
    ``my_window.view = some_gadget``.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    allow_vertical_resize : bool, default: True
        Whether window can be resized vertically.
    allow_horizontal_resize : bool, default: True
        Whether window can be resized horizontally.
    resize_min_height : int | None, default: None
        Minimum height window can be resized.
    resize_min_width : int | None, default: None
        Minimum width window can be resized.
    alpha : float, default: 1.0
        Transparency of gadget.
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
    view : Gadget
        The windowed gadget.
    title : str
        Title of window.
    is_focused : bool
        Whether gadget has focus.
    any_focused : bool
        Whether any gadget has focus.
    allow_vertical_resize : bool
        Whether window can be resized vertically.
    allow_horizontal_resize : bool
        Whether window can be resized horizontally.
    resize_min_height : int
        Minimum height window can be resized.
    resize_min_width : int
        Minimum width window can be resized.
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
    update_theme()
        Paint the gadget with current theme.
    focus()
        Focus gadget.
    blur()
        Un-focus gadget.
    focus_next()
        Focus next focusable gadget.
    focus_previous()
        Focus previous focusable gadget.
    on_focus()
        Update gadget when it gains focus.
    on_blur()
        Update gadget when it loses focus.
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
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_visible: bool = True,
        is_enabled: bool = True,
        is_transparent: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_visible=is_visible,
            is_enabled=is_enabled,
            is_transparent=is_transparent,
        )
        self._y_edge: Literal[-1, 0, 1] = 0
        self._x_edge: Literal[-1, 0, 1] = 0
        self._view = None
        self._titlebar = _TitleBar()
        self._top_border = Pane(size=(1, 1), size_hint={"width_hint": 1.0})
        self._bot_border = Pane(
            size=(1, 1),
            size_hint={"width_hint": 1.0},
            pos_hint={"y_hint": 1.0, "anchor": "bottom"},
        )
        self._left_border = Pane(
            pos=(1, 0),
            size=(1, 2),
            size_hint={"height_hint": 1.0, "height_offset": -2},
        )
        self._right_border = Pane(
            pos=(1, 0),
            size=(1, 2),
            size_hint={"height_hint": 1.0, "height_offset": -2},
            pos_hint={"x_hint": 1.0, "anchor": "right"},
        )
        self._background = Pane(
            pos=(1, 2),
            size_hint={
                "height_hint": 1.0,
                "width_hint": 1.0,
                "height_offset": -2,
                "width_offset": -4,
            },
        )
        self.add_gadgets(
            self._top_border,
            self._bot_border,
            self._left_border,
            self._right_border,
            self._background,
            self._titlebar,
        )
        self._title = ""
        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize
        self.resize_min_height = resize_min_height
        self.resize_min_width = resize_min_width
        self.alpha = alpha
        self.title = title

    @property
    def resize_min_height(self) -> int:
        """Minimum height gadget can be resized."""
        return self._resize_min_height

    @resize_min_height.setter
    def resize_min_height(self, min_height: int | None):
        if min_height is None:
            self._resize_min_height = 3
        else:
            self._resize_min_height = clamp(min_height, 3, None)

    @property
    def resize_min_width(self) -> int:
        """Minimum width gadget can be resized."""
        return self._resize_min_width

    @resize_min_width.setter
    def resize_min_width(self, min_width: int | None):
        w = 6 + str_width(self._title)
        if min_width is None:
            self._resize_min_width = w
        else:
            self._resize_min_width = clamp(min_width, w, None)

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._background.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._top_border.alpha = alpha
        self._bot_border.alpha = alpha
        self._left_border.alpha = alpha
        self._right_border.alpha = alpha
        self._background.alpha = alpha

    @property
    def view(self) -> Gadget | None:
        """The windowed gadget."""
        return self._view

    @view.setter
    def view(self, view: Gadget | None):
        if self._view is not None:
            self.remove_gadget(self._view)

        self._view = view

        if view is not None:
            view.size_hint = {}
            view.pos_hint = {}
            view.pos = 2, 2
            self.add_gadget(view)
            self.on_size()

    @property
    def title(self):
        """Title of window."""
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.width = str_width(title)
        self._titlebar._label.add_str(title)
        self.resize_min_width = self.resize_min_width

    def grab(self, mouse_event: MouseEvent):
        """Grab window."""
        super().grab(mouse_event)
        y, x = self.to_local(mouse_event.pos)
        self._y_edge = -1 if y == 0 else 1 if y == self.height - 1 else 0
        self._x_edge = (
            -1 if x in (0, 1) else 1 if x in (self.width - 2, self.width - 1) else 0
        )
        if self._y_edge == 0 and self._x_edge == 0:
            self.ungrab(mouse_event)

    def grab_update(self, mouse_event: MouseEvent):
        """Resize window if border is grabbed."""
        y, x = self.to_local(mouse_event.pos)
        dy = mouse_event.dy
        dx = mouse_event.dx
        if (
            (dy < 0 and y >= self.height - 1)
            or (dy > 0 and y <= 0)
            or (dx < 0 and x >= self.width - 1)
            or (dx > 0 and x <= 0)
        ):
            return

        verti = self.allow_vertical_resize and self._y_edge
        horiz = self.allow_horizontal_resize and self._x_edge
        h, w = self.size
        new_size = Size(
            clamp(h + verti * dy, self.resize_min_height, None),
            clamp(w + horiz * dx, self.resize_min_width, None),
        )
        self.size = new_size
        if self._y_edge == -1:
            self.top += h - new_size.height
        if self._x_edge == -1:
            self.left += w - new_size.width

    def update_theme(self):
        """Paint the gadget with current theme."""
        self._background.bg_color = self.color_theme.primary.bg

        if self.is_focused:
            fg, bg = self.color_theme.titlebar_normal
            border = self.color_theme.window_border_normal
        else:
            fg, bg = self.color_theme.titlebar_inactive
            border = self.color_theme.window_border_inactive

        self._titlebar.fg_color = fg
        self._titlebar.bg_color = bg
        self._titlebar._label.default_fg_color = fg
        self._titlebar._label.default_bg_color = bg
        self._titlebar._label.canvas["fg_color"] = fg
        self._titlebar._label.canvas["bg_color"] = bg
        self._top_border.bg_color = border
        self._bot_border.bg_color = border
        self._left_border.bg_color = border
        self._right_border.bg_color = border

    def on_size(self):
        """Resize view on resize."""
        h, w = self._size
        h -= 3
        w -= 4
        if self._view is not None:
            self._view.size = h, w
            self._view.is_visible = h > 0 and w > 0

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
            mouse_event.pos
        )
