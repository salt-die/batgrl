"""Draggable horizontal and vertical split layouts."""

from time import perf_counter
from typing import Literal

from ..colors import WHITE, Color, lerp_colors
from ..geometry.easings import in_quart, out_quart
from .behaviors.grabbable import Grabbable
from .gadget import Gadget, Point, PosHint, Size, SizeHint, clamp
from .pane import Pane

__all__ = ["HSplitLayout", "VSplitLayout", "Point", "Size"]

GRAY = Color(127, 127, 127)


class _Handle(Grabbable, Pane):
    def __init__(self, size_hint):
        super().__init__(size=(2, 2), size_hint=size_hint, alpha=0)

    def on_mouse(self, mouse_event):
        self.alpha = (self.is_grabbed or self.collides_point(mouse_event.pos)) * 0.5
        return super().on_mouse(mouse_event)

    @property
    def bg_color(self) -> Color:
        p = perf_counter() % 1.0
        if p < 0.5:
            return lerp_colors(GRAY, WHITE, in_quart(2.0 * p))
        return lerp_colors(WHITE, GRAY, out_quart(2.0 * p - 1.0))

    @bg_color.setter
    def bg_color(self, _):
        pass


class _HSplitHandle(_Handle):
    def grab_update(self, mouse_event):
        self.parent: HSplitLayout
        self.parent.split_row += mouse_event.dy


class _VSplitHandle(_Handle):
    def grab_update(self, mouse_event):
        self.parent: VSplitLayout
        self.parent.split_col += mouse_event.dx


class HSplitLayout(Gadget):
    r"""
    A horizontal split layout.

    Add gadgets to the :attr:``top_pane`` or :attr:``bottom_pane``, e.g.,
    ``my_hsplit.top_pane.add_gadget(my_gadget)``.

    If :attr:``top_min_height`` and :attr:``bottom_min_height`` can't both be satisfied,
    :attr:``split_anchor`` will determine which pane's height requirement is preferred.

    Parameters
    ----------
    split_row : int, default: 1
        Height of top pane. Height of bottom pane is ``self.width - split_row``.
    split_anchor : Literal["top", "bottom"], default: "top
        If gadget is resized, ``split_anchor`` determines which pane's height isn't
        changed.
    split_resizable : bool, default: True
        Whether split is resizable with a grabbable handle.
    top_min_height : int, default: 1
        Minimum height of top pane.
    bottom_min_height : int, default: 1
        Minimum height of bottom pane.
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
    top_pane : Gadget
        Container gadget for top side of split layout.
    bottom_pane : Gadget
        Container gadget for bottom side of split layout.
    split_row : int
        Height of top pane. Height of bottom pane is ``self.width - split_row``.
    split_anchor : Literal["top", "bottom"]
        If gadget is resized, ``split_anchor`` determines which pane's height isn't
        changed.
    split_resizable : bool
        Whether split is resizable with a grabbable handle.
    top_min_height : int
        Minimum height of top pane.
    bottom_min_height : int
        Minimum height of bottom pane.
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
        split_row: int = 1,
        split_anchor: Literal["top", "bottom"] = "top",
        split_resizable: bool = True,
        top_min_height: int = 1,
        bottom_min_height: int = 1,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
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

        self.top_pane = Gadget(size_hint={"width_hint": 1.0})
        """Container gadget for top side of split layout."""
        self.bottom_pane = Gadget(size_hint={"width_hint": 1.0})
        """Container gadget for bottom side of split layout."""
        self.handle = _HSplitHandle({"width_hint": 1.0})
        """Grabbable handle gadget used to resize split layout."""

        def adjust():
            self.bottom_pane.top = self.top_pane.bottom
            self.handle.top = self.top_pane.bottom - 1

        self.top_pane.bind("size", adjust)
        self.add_gadgets(self.top_pane, self.bottom_pane, self.handle)

        self.split_anchor = split_anchor
        """
        If gadget is resized, ``split_anchor`` determines which pane's height isn't
        changed.
        """
        self.split_resizable = split_resizable
        """Whether split is resizable with a grabbable handle."""
        self._top_min_height = top_min_height
        """Minimum height of top pane."""
        self._bottom_min_height = bottom_min_height
        """Minimum height of bottom pane."""
        self.split_row = split_row
        """Height of top pane."""

    @property
    def top_min_height(self) -> int:
        """Minimum height of top pane."""
        return self._top_min_height

    @top_min_height.setter
    def top_min_height(self, top_min_height: int):
        self._top_min_height = clamp(top_min_height, 0, None)
        self.split_row = self.split_row

    @property
    def bottom_min_height(self) -> int:
        """Minimum height of bottom pane."""
        return self._bottom_min_height

    @bottom_min_height.setter
    def bottom_min_height(self, bottom_min_height: int):
        self._bottom_min_height = clamp(bottom_min_height, 0, None)
        self.split_row = self.split_row

    @property
    def split_row(self) -> int:
        """Height of top pane."""
        return self.top_pane.height

    @split_row.setter
    def split_row(self, split_row: int):
        if (
            self.top_min_height <= split_row
            and self.bottom_min_height <= self.height - split_row
        ):
            self.top_pane.height = split_row
            self.bottom_pane.height = self.height - split_row
        elif split_row < self.top_min_height:
            if (
                self.split_anchor == "top"
                or self.bottom_min_height <= self.height - self.top_min_height
            ):
                self.top_pane.height = self.top_min_height
                self.bottom_pane.height = self.height - self.top_min_height
            else:
                self.bottom_pane.height = self.bottom_min_height
                self.top_pane.height = self.height - self.bottom_min_height
        elif (
            self.split_anchor == "bottom"
            or self.top_min_height <= self.height - self.bottom_min_height
        ):
            self.bottom_pane.height = self.bottom_min_height
            self.top_pane.height = self.height - self.bottom_min_height
        else:
            self.top_pane.height = self.top_min_height
            self.bottom_pane.height = self.height - self.top_min_height

    @property
    def split_resizable(self) -> bool:
        """Whether split is resizable with a grabbable handle."""
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        """Resize panes on resize."""
        if self.split_anchor == "top":
            self.split_row = self.split_row
        else:
            self.split_row = self.height - self.bottom_pane.height


class VSplitLayout(Gadget):
    r"""
    A vertical split layout.

    Add gadgets to the :attr:``left_pane`` or :attr:``right_pane``, e.g.,
    ``my_vsplit.left_pane.add_gadget(my_gadget)``.

    If :attr:``left_min_width`` and :attr:``right_min_width`` can't both be satisfied,
    :attr:``split_anchor`` will determine which pane's width requirement is preferred.

    Parameters
    ----------
    split_col : int, default: 1
        Width of left pane. Height of right pane is ``self.width - split_col``.
    split_anchor : Literal["left", "right"], default: "left"
        If gadget is resized, ``split_anchor`` determines which pane's width isn't
        changed.
    split_resizable : bool, default: True
        Whether split is resizable with a grabbable handle.
    left_min_width : int, default: 1
        Minimum width of left pane.
    right_min_width : int, default: 1
        Minimum width of right pane.
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
    left_pane : Gadget
        Container gadget for left side of split layout.
    right_pane : Gadget
        Container gadget for right side of split layout.
    split_col : int
        Width of left pane. Height of right pane is ``self.width - split_col``.
    split_anchor : Literal["left", "right"]
        If gadget is resized, ``split_anchor`` determines which pane's width isn't
        changed.
    split_resizable : bool
        Whether split is resizable with a grabbable handle.
    left_min_width : int
        Minimum width of left pane.
    right_min_width : int
        Minimum width of right pane.
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
        split_col: int = 1,
        split_anchor: Literal["left", "right"] = "left",
        split_resizable: bool = True,
        left_min_width: int = 1,
        right_min_width: int = 1,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
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

        self.left_pane = Gadget(size_hint={"height_hint": 1.0})
        """Container gadget for left side of split layout."""
        self.right_pane = Gadget(size_hint={"height_hint": 1.0})
        """Container gadget for right side of split layout."""
        self.handle = _VSplitHandle({"height_hint": 1.0})
        """Grabbable handle gadget used to resize split layout."""

        def adjust():
            self.right_pane.left = self.left_pane.right
            self.handle.left = self.left_pane.right - 1

        self.left_pane.bind("size", adjust)
        self.add_gadgets(self.left_pane, self.right_pane, self.handle)

        self.split_anchor = split_anchor
        """
        If gadget is resized, ``split_anchor`` determines which pane's width isn't
        changed.
        """
        self.split_resizable = split_resizable
        """ Whether split is resizable with a grabbable handle."""
        self._left_min_width = left_min_width
        """Minimum width of left pane."""
        self._right_min_width = right_min_width
        """Minimum width of right pane."""
        self.split_col = split_col
        """Width of left pane."""

    @property
    def left_min_width(self) -> int:
        """Minimum width of left pane."""
        return self._left_min_width

    @left_min_width.setter
    def left_min_width(self, left_min_width: int):
        self._left_min_width = clamp(left_min_width, 0, None)
        self.split_col = self.split_col

    @property
    def right_min_width(self) -> int:
        """Minimum width of right pane."""
        return self._right_min_width

    @right_min_width.setter
    def right_min_width(self, right_min_width: int):
        self._right_min_width = clamp(right_min_width, 0, None)
        self.split_col = self.split_col

    @property
    def split_col(self) -> int:
        """Width of left pane."""
        return self.left_pane.width

    @split_col.setter
    def split_col(self, split_col: int):
        if (
            self.left_min_width <= split_col
            and self.right_min_width <= self.width - split_col
        ):
            self.left_pane.width = split_col
            self.right_pane.width = self.width - split_col
        elif split_col < self.left_min_width:
            if (
                self.split_anchor == "left"
                or self.right_min_width <= self.width - self.left_min_width
            ):
                self.left_pane.width = self.left_min_width
                self.right_pane.width = self.width - self.left_min_width
            else:
                self.right_pane.width = self.right_min_width
                self.left_pane.width = self.width - self.right_min_width
        elif (
            self.split_anchor == "right"
            or self.left_min_width <= self.width - self.right_min_width
        ):
            self.right_pane.width = self.right_min_width
            self.left_pane.width = self.width - self.right_min_width
        else:
            self.left_pane.width = self.left_min_width
            self.right_pane.width = self.width - self.left_min_width

    @property
    def split_resizable(self) -> bool:
        """Whether split is resizable with a grabbable handle."""
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        """Resize panes on resize."""
        if self.split_anchor == "left":
            self.split_col = self.split_col
        else:
            self.split_col = self.width - self.right_pane.width
