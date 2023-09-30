"""
Draggable horizontal and vertical split layouts.
"""
from ..colors import AColor, ColorPair
from .behaviors.grabbable import Grabbable
from .graphic_widget import GraphicWidget
from .widget import (
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    Widget,
    clamp,
)

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


class _Handle(Grabbable, GraphicWidget):
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


class HSplitLayout(Widget):
    """
    A horizontal split layout. Add widgets to the :attr:`top_pane` or
    :attr:`bottom_pane`, e.g., ``my_hsplit.top_pane.add_widget(my_widget)``.

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
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    top_pane : Widget
        Container widget for top side of split.
    bottom_pane : Widget
        Container widget for bottom side of split.
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
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.top_pane = Widget(size_hint={"width_hint": 1.0})
        self.bottom_pane = Widget(size_hint={"width_hint": 1.0})

        self.handle = _HSplitHandle({"width_hint": 1.0})
        self.handle_color = handle_color

        def adjust():
            self.bottom_pane.top = self.handle.top = self.top_pane.bottom

        self.handle.subscribe(self.top_pane, "size", adjust)

        self.add_widgets(self.top_pane, self.bottom_pane, self.handle)

        self.split_resizable = split_resizable
        self.anchor_top_pane = anchor_top_pane

        self._min_split_height = min_split_height
        self.split_row = split_row

    @property
    def handle_color(self) -> AColor:
        return self.handle.default_color

    @handle_color.setter
    def handle_color(self, handle_color: AColor):
        self.handle.default_color = handle_color
        self.handle.texture[:] = handle_color
        self.handle.texture[-1] = 0

    @property
    def min_split_height(self) -> int:
        return self._min_split_height

    @min_split_height.setter
    def min_split_height(self, min_split_height: int):
        self._min_split_height = clamp(min_split_height, 1, None)
        self.split_row = self.split_row  # Clamp split and call `on_size`

    @property
    def split_row(self) -> int:
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
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        if self.anchor_top_pane:
            anchored = self.top_pane
            not_anchored = self.bottom_pane
        else:
            anchored = self.bottom_pane
            not_anchored = self.top_pane

        anchored.height = self.split_row
        not_anchored.height = self.height - self.split_row


class VSplitLayout(Widget):
    """
    A vertical split layout. Add widgets to the :attr:`left_pane` or :attr:`right_pane`,
    e.g., ``my_vsplit.left_pane.add_widget(my_widget)``.

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
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    left_pane : Widget
        Container widget for left side of split.
    right_pane : Widget
        Container widget for right side of split.
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
        Size of widget.
    height : int
        Height of widget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of widget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Widget | None
        Parent widget.
    children : list[Widget]
        Children widgets.
    is_transparent : bool
        True if widget is transparent.
    is_visible : bool
        True if widget is visible.
    is_enabled : bool
        True if widget is enabled.
    root : Widget | None
        If widget is in widget tree, return the root widget.
    app : App
        The running app.

    Methods
    -------
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
    collides_widget:
        True if other is within widget's bounding box.
    add_widget:
        Add a child widget.
    add_widgets:
        Add multiple child widgets.
    remove_widget:
        Remove a child widget.
    pull_to_front:
        Move to end of widget stack so widget is drawn last.
    walk_from_root:
        Yield all descendents of root widget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a widget property.
    unsubscribe:
        Unsubscribe to a widget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a widget property over time.
    on_add:
        Called after a widget is added to widget tree.
    on_remove:
        Called before widget is removed from widget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this widget and all descendents.
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
        background_char: str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.left_pane = Widget(size_hint={"height_hint": 1.0})
        self.right_pane = Widget(size_hint={"height_hint": 1.0})

        self.handle = _VSplitHandle({"height_hint": 1.0})
        self.handle_color = handle_color

        def adjust():
            self.right_pane.left = self.handle.left = self.left_pane.right

        self.handle.subscribe(self.left_pane, "size", adjust)

        self.add_widgets(self.left_pane, self.right_pane, self.handle)

        self.split_resizable = split_resizable
        self.anchor_left_pane = anchor_left_pane

        self._min_split_width = min_split_width
        self.split_col = split_col

    @property
    def handle_color(self) -> AColor:
        return self.handle.default_color

    @handle_color.setter
    def handle_color(self, handle_color: AColor):
        self.handle.default_color = handle_color
        self.handle.texture[:] = handle_color

    @property
    def min_split_width(self) -> int:
        return self._min_split_width

    @min_split_width.setter
    def min_split_width(self, min_split_width: int):
        self._min_split_width = clamp(min_split_width, 1, None)
        self.split_col = self.split_col

    @property
    def split_col(self) -> int:
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
        return self.handle.is_grabbable

    @split_resizable.setter
    def split_resizable(self, split_resizable: bool):
        self.handle.is_grabbable = split_resizable

    def on_size(self):
        if self.anchor_left_pane:
            anchored = self.left_pane
            not_anchored = self.right_pane
        else:
            anchored = self.right_pane
            not_anchored = self.left_pane

        anchored.width = self.split_col
        not_anchored.width = self.width - self.split_col
