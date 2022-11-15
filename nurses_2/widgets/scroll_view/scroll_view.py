"""
A scrollable view widget.
"""
from ...clamp import clamp
from ...io import KeyEvent, MouseEventType, MouseEvent
from ..behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget
from .scrollbars import _HorizontalBar, _VerticalBar


class ScrollView(GrabbableBehavior, Widget):
    """
    A scrollable view widget.

    The view can be set with the :attr:`view` property, e.g., ``my_scrollview.view = some_widget``.

    Parameters
    ----------
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    is_grabbable : bool, default: True
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    vertical_proportion : float, default: 0.0
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float, default: 0.0
        Horizontal scroll position as a proportion of total.
    is_grabbable : bool, default: True
        If False, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
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
    view : Widget | None
        The scrolled widget.
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    is_grabbable : bool
        Allow moving scroll view by dragging mouse.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
    view : Widget | None
        The scroll view's child.
    is_grabbable : bool
        If False, grabbable behavior is disabled.
    disable_ptf : bool
        If True, widget will not be pulled to front when grabbed.
    is_grabbed : bool
        True if widget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
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
    grab:
        Grab the widget.
    ungrab:
        Ungrab the widget.
    grab_update:
        Update widget with incoming mouse events while grabbed.
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
        allow_vertical_scroll=True,
        allow_horizontal_scroll=True,
        show_vertical_bar=True,
        show_horizontal_bar=True,
        is_grabbable=True,
        scrollwheel_enabled=True,
        arrow_keys_enabled=True,
        vertical_proportion=0.0,
        horizontal_proportion=0.0,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.allow_vertical_scroll = allow_vertical_scroll
        self.allow_horizontal_scroll = allow_horizontal_scroll
        self.is_grabbable = is_grabbable
        self.scrollwheel_enabled = scrollwheel_enabled
        self.arrow_keys_enabled = arrow_keys_enabled
        self._vertical_proportion = clamp(vertical_proportion, 0, 1)
        self._horizontal_proportion = clamp(horizontal_proportion, 0, 1)
        self._view = None
        self._vertical_bar = _VerticalBar(is_enabled=show_vertical_bar)
        self._horizontal_bar = _HorizontalBar(is_enabled=show_horizontal_bar)

        self.add_widgets(self._vertical_bar, self._horizontal_bar)

    @property
    def show_vertical_bar(self) -> bool:
        return self._vertical_bar.is_enabled

    @show_vertical_bar.setter
    def show_vertical_bar(self, show: bool):
        self._vertical_bar.is_enabled = show

    @property
    def show_horizontal_bar(self) -> bool:
        return self._horizontal_bar.is_enabled

    @show_horizontal_bar.setter
    def show_horizontal_bar(self, show: bool):
        self._horizontal_bar.is_enabled = show

    @property
    def view(self) -> Widget | None:
        return self._view

    @property
    def vertical_proportion(self):
        return self._vertical_proportion

    @vertical_proportion.setter
    def vertical_proportion(self, value):
        if self.allow_vertical_scroll:
            if self._view is None or self.total_vertical_distance <= 0:
                self._vertical_proportion = 0
            else:
                self._vertical_proportion = clamp(value, 0, 1)
                self._set_view_top()

            self._vertical_bar.indicator.update_geometry()

    @property
    def horizontal_proportion(self):
        return self._horizontal_proportion

    @horizontal_proportion.setter
    def horizontal_proportion(self, value):
        if self.allow_horizontal_scroll:
            if self._view is None or self.total_horizontal_distance <= 0:
                self._horizontal_proportion = 0
            else:
                self._horizontal_proportion = clamp(value, 0, 1)
                self._set_view_left()

            self._horizontal_bar.indicator.update_geometry()

    @property
    def total_vertical_distance(self) -> int:
        """
        Return difference between child height and scrollview height.
        """
        if self._view is None:
            return 0

        return self._view.height - self.height + self.show_horizontal_bar

    @property
    def total_horizontal_distance(self) -> int:
        """
        Return difference between child width and scrollview width.
        """
        if self._view is None:
            return 0

        return self._view.width - self.width + self.show_vertical_bar * 2

    def _set_view_top(self):
        """
        Set the top-coordinate of the view.
        """
        if self.total_vertical_distance <= 0:
            self._view.top = 0
        else:
            self._view.top = -round(self.vertical_proportion * self.total_vertical_distance)

    def _set_view_left(self):
        """
        Set the left-coordinate of the view.
        """
        if self.total_horizontal_distance <= 0:
            self._view.left = 0
        else:
            self._view.left = -round(self.horizontal_proportion * self.total_horizontal_distance)

    def _set_view_pos(self):
        """
        Set position of the view.
        """
        self._set_view_top()
        self._set_view_left()

    @property
    def view(self) -> Widget | None:
        return self._view

    @view.setter
    def view(self, view: Widget | None):
        if self._view is not None:
            self.remove_widget(self._view)

        self._view = view

        if view is not None:
            self.add_widget(view)

            self.children.insert(0, self.children.pop())  # Move view to top of view stack.
            self.subscribe(view, "size", self._set_view_pos)
            self._set_view_pos()

    def remove_widget(self, widget: Widget):
        if widget is self._view:
            self._view = None
            self.unsubscribe(widget, "size")

        super().remove_widget(widget)

    def on_size(self):
        if self._view is not None:
            self._set_view_pos()

    def on_key(self, key_event: KeyEvent):
        if not self.arrow_keys_enabled:
            return False

        match key_event.key:
            case "up":
                self._scroll_up()
            case "down":
                self._scroll_down()
            case "left":
                self._scroll_left()
            case "right":
                self._scroll_right()
            case _:
                return super().on_key(key_event)

        return True

    def grab_update(self, mouse_event: MouseEvent):
        self._scroll_up(self.mouse_dy)
        self._scroll_left(self.mouse_dx)

    def _scroll_left(self, n=1):
        if self._view is not None:
            if self.total_horizontal_distance > 0:
                self.horizontal_proportion = clamp((-self.view.left - n) / self.total_horizontal_distance, 0, 1)
            else:
                self.horizontal_proportion = 0

    def _scroll_right(self, n=1):
        self._scroll_left(-n)

    def _scroll_up(self, n=1):
        if self._view is not None:
            if self.total_vertical_distance > 0:
                self.vertical_proportion = clamp((-self.view.top - n) / self.total_vertical_distance, 0, 1)
            else:
                self.vertical_proportion = 0

    def _scroll_down(self, n=1):
        self._scroll_up(-n)

    def on_mouse(self, mouse_event: MouseEvent):
        if (
            self.scrollwheel_enabled
            and self.collides_point(mouse_event.position)
        ):
            match mouse_event.event_type:
                case MouseEventType.SCROLL_UP:
                    self._scroll_up()
                    return True
                case MouseEventType.SCROLL_DOWN:
                    self._scroll_down()
                    return True

        return super().on_mouse(mouse_event)
