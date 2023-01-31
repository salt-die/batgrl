"""
A movable, resizable window widget.
"""
import numpy as np
from wcwidth import wcswidth

from ..clamp import clamp
from ..colors import AColor
from .behaviors.focus_behavior import FocusBehavior
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.grab_resize_behavior import GrabResizeBehavior
from .behaviors.themable import Themable
from .text_widget import TextWidget
from .graphic_widget import GraphicWidget
from .widget import Widget, Anchor

__all__ = "Window",


class _TitleBar(GrabbableBehavior, Widget):
    def __init__(self):
        super().__init__(pos=(1, 2), disable_ptf=True, is_transparent=False, background_char=" ")

        self._label = TextWidget(pos_hint=(None, .5), anchor=Anchor.TOP_CENTER)
        self.add_widget(self._label)

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


class Window(Themable, FocusBehavior, GrabResizeBehavior, GraphicWidget):
    """
    A movable, resizable window widget.

    The view can be set with the :attr:`view` property, e.g., ``my_window.view = some_widget``.

    Parameters
    ----------
    title : str, default: ""
        Title of window.
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    grab_resize_min_height : int | None, default: None
        Minimum height widget can be resized by grabbing. Minimum
        height will never be less than 3.
    grab_resize_min_width : int | None, default: None
        Minimum width widget can be resized by grabbing. Minimum
        width will never be less than 6 + column width of title.
    border_alpha : float, default: 1.0
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor, default: TRANSPARENT
        Color of border.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If widget is transparent, the alpha channel of the underlying texture will be multiplied by this
        value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: Interpolation.LINEAR
        Interpolation used when widget is resized.
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
    view : Widget
        The windowed widget.
    title : str
        Title of window.
    ptf_on_focus : bool
        Pull widget to front when it gains focus.
    is_focused : bool
        Return True if widget has focus.
    any_focused : bool
        Return True if any widget has focus.
    allow_vertical_resize : bool
        Allow vertical resize.
    allow_horizontal_resize : bool
        Allow horizontal resize.
    grab_resize_min_height : int
        Minimum height widget can be resized by grabbing.
    grab_resize_min_width : int
        Minimum width widget can be resized by grabbing.
    border_alpha : float
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor
        Color of border.
    texture : numpy.ndarray
        uint8 RGBA color array.
    default_color : AColor
        Default texture color.
    alpha : float
        Transparency of widget if :attr:`is_transparent` is true.
    interpolation : Interpolation
        Interpolation used when widget is resized.
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
    update_theme:
        Paint the widget with current theme.
    focus:
        Focus widget.
    blur:
        Un-focus widget.
    focus_next:
        Focus next focusable widget.
    focus_previous:
        Focus previous focusable widget.
    on_focus:
        Called when widget is focused.
    on_blur:
        Called when widget loses focus.
    pull_border_to_front:
        Pull borders to the front.
    to_png:
        Write :attr:`texture` to provided path as a `png` image.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
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

    Notes
    -----
    If not given or too small, :attr:`grab_resize_min_height` and :attr:`grab_resize_min_width` will
    be set large enough so that the border and title are visible.

    As the window is resized, the :attr:`view` will be resized to fit within the window's borders,
    but non-`None` size hints of the view are still respected which can have unexpected results.
    It is recommended to use views with no size hints.
    """
    def __init__(self, title="", **kwargs):
        self._title = title

        super().__init__(**kwargs)

        self._view = None
        self._titlebar = _TitleBar()
        self.add_widget(self._titlebar)
        self.title = title

    @property
    def grab_resize_min_height(self) -> int:
        return self._grab_resize_min_height

    @grab_resize_min_height.setter
    def grab_resize_min_height(self, min_height: int | None):
        if min_height is None:
            self._grab_resize_min_height = 3
        else:
            self._grab_resize_min_height = clamp(min_height, 3, None)

    @property
    def grab_resize_min_width(self) -> int:
        return self._grab_resize_min_width

    @grab_resize_min_width.setter
    def grab_resize_min_width(self, min_width: int | None):
        w = 6 + wcswidth(self._title)
        if min_width is None:
            self._grab_resize_min_width = w
        else:
            self._grab_resize_min_width = clamp(min_width, w, None)

    @property
    def view(self) -> Widget | None:
        """
        The windowed widget.
        """
        return self._view

    @view.setter
    def view(self, view: Widget | None):
        if self._view is not None:
            self.remove_widget(self._view)

        self._view = view

        if view is not None:
            view.pos = 2, 2
            self.add_widget(view)
            self.on_size()

    def on_size(self):
        h, w = self._size
        self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)
        self.texture[4: -2, 2: -2] = self.default_color

        if self._view is not None:
            if self._view.size_hint == (None, None):
                self._view.size = h - 3, w - 4
            elif self._view.height_hint is None:
                self._view.height = h - 3
            elif self._view.width_hint is None:
                self._view.width = w - 4

    @property
    def title(self):
        return self._title

    @title.setter
    def title(self, title: str):
        self._title = title
        self._titlebar._label.width = wcswidth(title)
        self._titlebar._label.add_str(title)
        self.grab_resize_min_width = self.grab_resize_min_width

    def update_theme(self):
        self.default_color = AColor(*self.color_theme.primary.bg_color)
        self.texture[4: -2, 2: -2] = self.default_color

        if self.is_focused:
            title_color = self.color_theme.titlebar_normal
            self._titlebar.background_color_pair = title_color
            self._titlebar._label.default_color_pair = title_color
            self._titlebar._label.colors[:] = title_color

            self.border_color = self.color_theme.border_normal
        else:
            title_color = self.color_theme.titlebar_inactive
            self._titlebar.background_color_pair = title_color
            self._titlebar._label.default_color_pair = title_color
            self._titlebar._label.colors[:] = title_color

            self.border_color = self.color_theme.border_inactive

    def on_focus(self):
        self.update_theme()

    def on_blur(self):
        self.update_theme()

    def dispatch_mouse(self, mouse_event):
        return super().dispatch_mouse(mouse_event) or self.collides_point(mouse_event.position)
