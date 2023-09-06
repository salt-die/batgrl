"""
A widget for static multi-line text.
"""
from ..clamp import clamp
from .behaviors.themable import Themable
from .text_widget import TextWidget
from .widget import Widget, Size

# TODO: Set text with limited markdown.


class TextPanel(Themable, TextWidget):
    """
    A widget for static multi-line text.

    Text can be set by setting the `text` attribute. The read-only attribute :attr:`minimum_panel_size`
    is the minimum size the panel must be to show all text. This can be used to set the size of the
    panel, e.g., ``my_panel.size = my_panel.minimum_panel_size``.

    Parameters
    ----------
    text : str, default: ""
        Panel text.
    padding_y: int, default: 1
        Padding on top and bottom of panel.
    padding_x: int, default: 1
        Padding on the left and right of panel.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width grapheme.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
        Default color of widget.
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
        If true, background color and whitespace in text widget won't be painted.
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
        Panel text.
    padding_y: int
        Padding on top and bottom of panel.
    padding_x: int
        Padding on the left and right of panel.
    minimum_panel_size : Size
        Minimum size needed to show all text.
    text_container : TextWidget
        Child widget that contains the panel text.
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str
        Default background character.
    default_color_pair : ColorPair
        Default color pair of widget.
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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
    add_border:
        Add a border to the widget.
    normalize_canvas:
        Ensure column width of text in the canvas is equal to widget width.
    add_str:
        Add a single line of text to the canvas.
    set_text:
        Resize widget to fit text, erase canvas, then fill canvas with text.
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
    def __init__(self, *, text: str="", padding_y: int=1, padding_x: int=1, **kwargs):
        super().__init__(**kwargs)

        self.text_container = TextWidget()

        self._panel = Widget()
        self._panel.add_widget(self.text_container)

        self.add_widget(self._panel)

        self._padding_y = clamp(padding_y, 0, None)
        self._padding_x = clamp(padding_x, 0, None)
        self._update_padding()

        self.text = text

    @property
    def padding_y(self) -> int:
        return self._padding_y

    @padding_y.setter
    def padding_y(self, padding_y: int):
        self._padding_y = clamp(padding_y, 0, None)
        self._update_padding()

    @property
    def padding_x(self) -> int:
        return self._padding_x

    @padding_x.setter
    def padding_x(self, padding_x: int):
        self._padding_x = clamp(padding_x, 0, None)
        self._update_padding()

    def _update_padding(self):
        h, w = self.size
        self._panel.size = h - 2 * self._padding_y, w - 2 * self._padding_x
        self._panel.pos = self._padding_y, self._padding_x

    @property
    def text(self) -> str:
        return self._text

    @text.setter
    def text(self, text: str):
        self._text = text
        self.text_container.set_text(text)

    @property
    def minimum_panel_size(self) -> Size:
        """
        Minimum size needed for panel to show all text.
        """
        h, w = self.text_container.size
        return Size(h + 2 * self.padding_y, w + 2 * self.padding_x)

    def on_size(self):
        super().on_size()
        self._update_padding()

    def update_theme(self):
        panel = self.color_theme.panel
        self.colors[:] = panel
        self.default_color_pair = panel
        self._panel.background_color_pair = panel
        self.text_container.colors[:] = panel
        self.text_container.default_color_pair = panel
