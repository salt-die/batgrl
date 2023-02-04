from collections.abc import Callable

from wcwidth import wcswidth

from ..colors import lerp_colors, WHITE
from ..io import Key, KeyEvent, Mods, MouseButton, MouseEvent, PasteEvent
from .behaviors.focus_behavior import FocusBehavior
from .behaviors.grabbable_behavior import GrabbableBehavior
from .behaviors.themable import Themable
from .text_widget import TextWidget
from .widget import Widget


class TextContainer(Themable, Widget):
    """
    A text_container widget for single-line editable text.

    Supports pasting, mouse selection, and cursor navigation.

    Parameters
    ----------
    default_text : str, default: ""
        Default text displayed.
    max_chars : int | None, default: None
        Maximum allowed number of characters in text_container.
    ptf_on_focus : bool, default: True
        Pull widget to front when it gains focus.
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
    text : str
        The text_container's text.
    max_chars : int | None, default: None
        Maximum allowed number of characters in text_container.
    ptf_on_focus : bool
        Pull widget to front when it gains focus.
    is_focused : bool
        Return True if widget has focus.
    any_focused : bool
        Return True if any widget has focus.
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
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
    def __init__(self, default_text: str="", max_chars: int | None=None, **kwargs):
        super().__init__(**kwargs)

        self.max_chars = max_chars
        self._line_length = 0

        self._box = TextWidget(size=(1, 1))

        self.text = default_text

        self.add_widget(self._box)

    def update_theme(self):
        primary = self.color_theme.primary
        self._box.colors[:] = primary
        self._box.default_color_pair = primary
        self.background_color_pair = primary

    def on_size(self):
        if self.width > self._box.width:
            self._box.width = self.width
        elif self.width < self._box.width:
            self._box.width = max(self.width, self._line_length + 1)

    @property
    def text(self) -> str:
        return "".join(self._box.canvas[0, :self._line_length])

    @text.setter
    def text(self, text: str):
        text = text.replace("\n", " ")
        self._line_length = wcswidth(text)

        box = self._box
        box.canvas[:] = " "
        box.width = max(self._line_length + 1, self.width)
        box.add_str(text)
        self.cursor = self._line_length
