"""
Draggable horizontal and vertical split layouts.
"""
from ..clamp import clamp
from ..colors import AColor
from .behaviors.grabbable_behavior import GrabbableBehavior
from .graphic_widget import GraphicWidget
from .widget import Widget

__all__ = "HSplitLayout", "VSplitLayout",

AGRAY = AColor(127, 127, 127, 127)


class _Handle(GrabbableBehavior, GraphicWidget):
    def __init__(self, size_hint):
        super().__init__(
            size=(1, 1),
            size_hint=size_hint,
            is_visible=False,
        )

    def on_mouse(self, mouse_event):
        self.is_visible = (
            self.is_grabbable
            and self.is_grabbed or self.collides_point(mouse_event.position)
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
    A horizontal split layout. Add widgets to the :attr:`top_pane` or :attr:`bottom_pane`,
    e.g., ``my_hsplit.top_pane.add_widget(my_widget)``.

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
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

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
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
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
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
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
        Yield all descendents (or ancestors if `reverse` is True).
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
        split_row: int=1,
        min_split_height: int=1,
        anchor_top_pane: bool=True,
        split_resizable: bool=True,
        handle_color: AColor=AGRAY,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.top_pane = Widget(size_hint=(None, 1.0))
        self.bottom_pane = Widget(size_hint=(None, 1.0))

        self.handle = _HSplitHandle((None, 1.0))
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
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

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
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
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
    update_geometry:
        Called when parent is resized. Applies size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
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
        Yield all descendents (or ancestors if `reverse` is True).
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
        split_col: int=1,
        min_split_width: int=1,
        anchor_left_pane: bool=True,
        split_resizable: bool=True,
        handle_color: AColor=AGRAY,
        **kwargs
    ):
        super().__init__(**kwargs)

        self.left_pane = Widget(size_hint=(1.0, None))
        self.right_pane = Widget(size_hint=(1.0, None))

        self.handle = _VSplitHandle((1.0, None))
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
