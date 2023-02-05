"""
A progress bar widget.
"""
from ..clamp import clamp
from .behaviors.themable import Themable
from .text_widget import TextWidget
from .widget import subscribable

FULL_BLOCK = "█"
VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉"


class ProgressBar(Themable, TextWidget):
    """
    A progress bar widget.

    Parameters
    ----------
    is_horizontal : bool, default: True
        If true, the bar will progress to the right, else
        the bar will progress upwards.
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
    progress : float
        Current progress as a value between `0.0` and `1.0`.
    is_horizontal : bool
        If true, the bar will progress to the right, else
        the bar will progress upwards.
    canvas : numpy.ndarray
        The array of characters for the widget.
    colors : numpy.ndarray
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str, default: " "
        Default background character.
    default_color_pair : ColorPair, default: WHITE_ON_BLACK
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
    """
    def __init__(self, is_horizontal: bool=True, **kwargs):
        super().__init__(**kwargs)
        self._is_horizontal = is_horizontal
        self._progress = 0.0

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    @subscribable
    def progress(self, progress: float):
        self._progress = clamp(progress, 0.0, 1.0)
        self._update_canvas()

    @property
    def is_horizontal(self) -> bool:
        return self._is_horizontal

    @is_horizontal.setter
    def is_horizontal(self, is_horizontal: bool):
        self._is_horizontal = is_horizontal
        self._update_canvas()

    def on_size(self):
        self._update_canvas()

    def update_theme(self):
        self._update_canvas()

    def _update_canvas(self):
        self.colors[:] = self.color_theme.button_normal

        if self.is_horizontal:
            fill, partial = divmod(self.progress * self.width, 1)
            fill_length, partial_index = int(fill), int(len(HORIZONTAL_BLOCKS) * partial)
            self.canvas["char"][:, :fill_length] = FULL_BLOCK

            if fill_length < self.width:
                self.canvas["char"][:, fill_length] = HORIZONTAL_BLOCKS[partial_index]
                self.canvas["char"][:, fill_length + 1:] = HORIZONTAL_BLOCKS[0]
        else:
            fill, partial = divmod(self.progress * self.height, 1)
            fill_length, partial_index = int(fill), int(len(VERTICAL_BLOCKS) * partial)
            chars = self.canvas["char"][::-1]
            chars[:fill_length] = FULL_BLOCK

            if fill_length < self.height:
                chars[fill_length: fill_length + 1] = VERTICAL_BLOCKS[partial_index]
                chars[fill_length + 1:] = VERTICAL_BLOCKS[0]
