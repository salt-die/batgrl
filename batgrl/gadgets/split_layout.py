"""Draggable horizontal and vertical split layouts."""
from ..colors import AColor
from .behaviors.grabbable import Grabbable
from .gadget import Gadget
from .gadget_base import (
    GadgetBase,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
)
from .graphics import Graphics

__all__ = [
    "HSplitLayout",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "VSplitLayout",
]

AGRAY = AColor(127, 127, 127, 127)


class _Handle(Grabbable, Graphics):
    def __init__(self, size_hint):
        super().__init__(
            size=(1, 1),
            size_hint=size_hint,
            is_visible=False,
        )

    def on_mouse(self, mouse_event):
        self.is_visible = (
            self.is_grabbable
            and self.is_grabbed
            or self.collides_point(mouse_event.position)
        )
        return super().on_mouse(mouse_event)


class _HSplitHandle(_Handle):
    def on_size(self):
        super().on_size()
        self.texture[-1] = 0

    def grab_update(self, mouse_event):
        if self.parent.anchor_top_pane:
            self.parent.split_row += self.mouse_dy
        else:
            self.parent.split_row -= self.mouse_dy


class _VSplitHandle(_Handle):
    def grab_update(self, mouse_event):
        if self.parent.anchor_left_pane:
            self.parent.split_col += self.mouse_dx
        else:
            self.parent.split_col -= self.mouse_dx


class HSplitLayout(GadgetBase):
    r"""
    A horizontal split layout. Add gadgets to the :attr:`top_pane` or
    :attr:`bottom_pane`, e.g., ``my_hsplit.top_pane.add_gadget(my_gadget)``.

    Parameters
    ----------
    split_row : int, default: 1
        Height of top pane if :attr:`anchor_top_pane` is true, else
        height of right pane.
    min_split_height : int, default: 1
        Minimum height of either pane.
    anchor_top_pane : bool, default: True
        If true, :attr:`split_row` will be calculated from the top,
        else from the bottom.
    split_resizable : bool, default: True
        If true, the split will be resizable with a grabbable
        handle.
    handle_color : AColor, default: AGRAY
        Color of the resize handle.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    top_pane : Gadget
        Container gadget for top side of split.
    bottom_pane : Gadget
        Container gadget for bottom side of split.
    handle_color : AColor
        Color of the resize handle.
    split_resizable : bool
        True if split is resizable with a grabbable handle.
    anchor_top_pane : bool
        If true, :attr:`split_row` is calculated from the top.
    split_row : int
        Height of top pane if :attr:`anchor_top_pane` is true, else
        height of right pane.
    min_split_height : int
        Minimum height of either pane.
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
    """

    def __init__(
        self,
        *,
        split_row: int = 1,
        min_split_height: int = 1,
        anchor_top_pane: bool = True,
        split_resizable: bool = True,
        handle_color: AColor = AGRAY,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
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
        self.bottom_pane = Gadget(size_hint={"width_hint": 1.0})

        self.handle = _HSplitHandle({"width_hint": 1.0})
        self.handle_color = handle_color

        def adjust():
            self.bottom_pane.top = self.handle.top = self.top_pane.bottom

        self.handle.subscribe(self.top_pane, "size", adjust)

        self.add_gadgets(self.top_pane, self.bottom_pane, self.handle)

        self.split_resizable = split_resizable
        self.anchor_top_pane = anchor_top_pane

        self._min_split_height = min_split_height
        self.split_row = split_row

    @property
    def handle_color(self) -> AColor:
        """Color of the resize handle."""
        return self.handle.default_color

    @handle_color.setter
    def handle_color(self, handle_color: AColor):
        self.handle.default_color = handle_color
        self.handle.texture[:] = handle_color
        self.handle.texture[-1] = 0

    @property
    def min_split_height(self) -> int:
        """Minimum height of either pane."""
        return self._min_split_height

    @min_split_height.setter
    def min_split_height(self, min_split_height: int):
        self._min_split_height = clamp(min_split_height, 1, None)
        self.split_row = self.split_row  # Clamp split and call `on_size`

    @property
    def split_row(self) -> int:
        """
        Height of top pane if :attr:`anchor_top_pane` is true, else height of
        right pane.
        """
        return self._split_col

    @split_row.setter
    def split_row(self, split_row: int):
        min_height = self.min_split_height
        self._split_col = clamp(
            split_row,
            min_height,
            max(self.height - min_height, min_height),
        )
        self.on_size()

    @property
    def split_resizable(self) -> bool:
        """True if split is resizable with a grabbable handle."""
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        """Resize panes on resize."""
        if self.anchor_top_pane:
            anchored = self.top_pane
            not_anchored = self.bottom_pane
        else:
            anchored = self.bottom_pane
            not_anchored = self.top_pane

        anchored.height = self.split_row
        not_anchored.height = self.height - self.split_row


class VSplitLayout(GadgetBase):
    r"""
    A vertical split layout. Add gadgets to the :attr:`left_pane` or :attr:`right_pane`,
    e.g., ``my_vsplit.left_pane.add_gadget(my_gadget)``.

    Parameters
    ----------
    split_col : int, default: 1
        Width of left pane if :attr:`anchor_left_pane` is true, else
        width of right pane.
    min_split_width : int, default: 1
        Minimum width of either pane.
    anchor_left_pane : bool, default: True
        If true, :attr:`split_col` will be calculated from the left,
        else from the right.
    split_resizable : bool, default: True
        If true, the split will be resizable with a grabbable
        handle.
    handle_color : AColor, default: AGRAY
        Color of the resize handle.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    left_pane : Gadget
        Container gadget for left side of split.
    right_pane : Gadget
        Container gadget for right side of split.
    handle_color : AColor
        Color of the resize handle.
    split_resizable : bool
        True if split is resizable with a grabbable handle.
    anchor_left_pane : bool
        If true, :attr:`split_col` is calculated from the left.
    split_col : int
        Width of left pane if :attr:`anchor_left_pane` is true, else
        width of right pane.
    min_split_width : int
        Minimum width of either pane.
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
    """

    def __init__(
        self,
        split_col: int = 1,
        min_split_width: int = 1,
        anchor_left_pane: bool = True,
        split_resizable: bool = True,
        handle_color: AColor = AGRAY,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
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
        self.right_pane = Gadget(size_hint={"height_hint": 1.0})

        self.handle = _VSplitHandle({"height_hint": 1.0})
        self.handle_color = handle_color

        def adjust():
            self.right_pane.left = self.handle.left = self.left_pane.right

        self.handle.subscribe(self.left_pane, "size", adjust)

        self.add_gadgets(self.left_pane, self.right_pane, self.handle)

        self.split_resizable = split_resizable
        self.anchor_left_pane = anchor_left_pane

        self._min_split_width = min_split_width
        self.split_col = split_col

    @property
    def handle_color(self) -> AColor:
        """Color of the resize handle."""
        return self.handle.default_color

    @handle_color.setter
    def handle_color(self, handle_color: AColor):
        self.handle.default_color = handle_color
        self.handle.texture[:] = handle_color

    @property
    def min_split_width(self) -> int:
        """Minimum width of either pane."""
        return self._min_split_width

    @min_split_width.setter
    def min_split_width(self, min_split_width: int):
        self._min_split_width = clamp(min_split_width, 1, None)
        self.split_col = self.split_col

    @property
    def split_col(self) -> int:
        """
        Width of left pane if :attr:`anchor_left_pane` is true, else width of
        right pane.
        """
        return self._split_row

    @split_col.setter
    def split_col(self, split_col: int):
        min_width = self.min_split_width
        self._split_row = clamp(
            split_col,
            min_width,
            max(self.width - min_width, min_width),
        )
        self.on_size()

    @property
    def split_resizable(self) -> bool:
        """True if split is resizable with a grabbable handle."""
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        """Resize panes on resize."""
        if self.anchor_left_pane:
            anchored = self.left_pane
            not_anchored = self.right_pane
        else:
            anchored = self.right_pane
            not_anchored = self.left_pane

        anchored.width = self.split_col
        not_anchored.width = self.width - self.split_col
