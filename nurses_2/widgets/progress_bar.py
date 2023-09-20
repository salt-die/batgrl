"""
A progress bar widget.
"""
import asyncio
from itertools import chain, cycle

from ..clamp import clamp
from ._smooth_bars import create_horizontal_bar, create_vertical_bar
from .behaviors.themable import Themable
from .text_widget import TextWidget, style_char
from .widget import subscribable


class ProgressBar(Themable, TextWidget):
    """
    A progress bar widget.

    Setting :attr:`progress` to `None` will start a "loading" animation; otherwise
    setting to a value between `0.0` and `1.0` will update the bar.

    Parameters
    ----------
    animation_delay : float, default: 1/60
        Time between loading animation updates.
    is_horizontal : bool, default: True
        If true, the bar will progress to the right, else the bar will progress upwards.
    default_char : str, default: " "
        Default background character. This should be a single unicode half-width
        grapheme.
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
    anchor : Anchor, default: "center"
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
    progress : float | None
        Current progress as a value between `0.0` and `1.0` or `None. If `None`, then
        progress bar will start a "loading" animation.
    animation_delay : float
        Time between loading animation updates.
    is_horizontal : bool
        If true, the bar will progress to the right, else
        the bar will progress upwards.
    canvas : NDArray[Char]
        The array of characters for the widget.
    colors : NDArray[np.uint8]
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

    def __init__(
        self, *, is_horizontal: bool = True, animation_delay: float = 1 / 60, **kwargs
    ):
        super().__init__(**kwargs)
        self.animation_delay = animation_delay
        self._is_horizontal = is_horizontal
        self._progress = None

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    @subscribable
    def progress(self, progress: float):
        if getattr(self, "_loading_task", False):
            self._loading_task.cancel()

        if progress is None:
            self._progress = progress
            self._loading_task = asyncio.create_task(self._loading_animation())
        else:
            self._progress = clamp(progress, 0.0, 1.0)
            self._repaint_progress_bar()

    @property
    def is_horizontal(self) -> bool:
        return self._is_horizontal

    @is_horizontal.setter
    def is_horizontal(self, is_horizontal: bool):
        self._is_horizontal = is_horizontal
        self.progress = self.progress  # Trigger a repaint by setting property.

    def _paint_small_horizontal_bar(self, progress):
        bar_width = max(1, (self.width - 1) // 2)
        x, offset = divmod(progress * (self.width - bar_width), 1)
        x = int(x)
        smooth_bar = create_horizontal_bar(bar_width, 1, offset)

        self.canvas[:] = style_char(self.default_char)
        self.canvas["char"][:, x : x + len(smooth_bar)] = smooth_bar
        self.colors[:] = self.color_theme.progress_bar
        if offset != 0:
            self.colors[:, x] = self.color_theme.progress_bar.reversed()

    def _paint_small_vertical_bar(self, progress):
        bar_height = max(1, (self.height - 1) // 2)
        y, offset = divmod(progress * (self.height - bar_height), 1)
        y = int(y)
        smooth_bar = create_vertical_bar(bar_height, 1, offset)

        self.canvas[:] = style_char(self.default_char)
        try:
            self.canvas["char"][::-1][y : y + len(smooth_bar)].T[:] = smooth_bar
        except Exception as e:
            raise SystemExit(bar_height, progress, offset, smooth_bar) from e
        self.colors[:] = self.color_theme.progress_bar
        if offset != 0:
            self.colors[::-1][y] = self.color_theme.progress_bar.reversed()

    async def _loading_animation(self):
        if (
            self.is_horizontal
            and self.width < 3
            or not self.is_horizontal
            and self.height < 3
        ):
            return

        self.canvas[:] = style_char(self.default_char)

        if self._is_horizontal:
            HSTEPS = 8 * self.width
            for i in cycle(chain(range(HSTEPS + 1), range(HSTEPS)[::-1])):
                self._paint_small_horizontal_bar(i / HSTEPS)
                await asyncio.sleep(self.animation_delay)
        else:
            VSTEPS = 8 * self.height
            for i in cycle(chain(range(VSTEPS + 1), range(VSTEPS)[::-1])):
                self._paint_small_vertical_bar(i / VSTEPS)
                await asyncio.sleep(self.animation_delay)

    def on_add(self):
        super().on_add()
        self.progress = self.progress  # Trigger a repaint by setting property.

    def on_remove(self):
        super().on_remove()
        if task := getattr(self, "_loading_task", False):
            task.cancel()

    def on_size(self):
        super().on_size()
        self.progress = self.progress  # Trigger a repaint by setting property.

    def update_theme(self):
        self.colors[:] = self.color_theme.progress_bar
        self.default_color_pair = self.color_theme.progress_bar

    def _repaint_progress_bar(self):
        self.canvas[:] = style_char(self.default_char)
        if self.is_horizontal:
            smooth_bar = create_horizontal_bar(self.width, self.progress)
            self.canvas["char"][:, : len(smooth_bar)] = smooth_bar
        else:
            smooth_bar = create_vertical_bar(self.height, self.progress)
            self.canvas["char"][::-1][: len(smooth_bar)].T[:] = smooth_bar
