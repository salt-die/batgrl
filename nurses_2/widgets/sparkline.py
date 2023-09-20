from collections.abc import Sequence
from numbers import Real

import numpy as np
from numpy.typing import NDArray

from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair, lerp_colors
from ..io import MouseEvent
from ._smooth_bars import create_vertical_bar
from .text_widget import TextWidget, add_text, style_char
from .widget import Widget

__all__ = ("Sparkline",)

DEFAULT_TOOLTIP_COLORS = DEFAULT_COLOR_THEME.primary
DEFAULT_MIN_COLOR = Color.from_hex("1B244B")
DEFAULT_MAX_COLOR = Color.from_hex("4D67FF")
DEFAULT_HIGHLIGHT_COLOR = Color.from_hex("7281FF")


def _get_float_text(value: float) -> str:
    text = f"{value:8.2f}"
    if len(text) > 8:
        return f"{value:3.2e}"
    return text


class _Tooltip(TextWidget):
    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self.is_enabled = self.selector.is_enabled = False


class _BinSelector(Widget):
    def render(self, _, colors_view, source: tuple[slice, slice]):
        colors_view[source][..., :3] = self.parent.highlight_color


class Sparkline(TextWidget):
    """
    A sparkline widget for displaying sequential data.

    Parameters
    ----------
    data : Sequence[Real] | None, default: None
        Data for the sparkline.
    min_color : Color, default: DEFAULT_MIN_COLOR
        Color of minimum value of the sparkline.
    max_color : Color, default: DEFAULT_MAX_COLOR
        Color of the maximum value of the sparkline.
    show_tooltip : bool, default: True
        Whether to show tooltip.
    tooltip_color_pair : ColorPair, default: DEFAULT_TOOLTIP_COLORS
        Color pair for tooltip.
    highlight_color : Color, default: DEFAULT_HIGHLIGHT_COLOR
        Color of highlighted value of the sparkline.
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
    data : NDArray[np.float64]
        Data for the sparkline. This can be set with a `Sequence[Real]` or `None`, but
        will be converted into a (possibly empty) numpy array.
    min_color : Color
        Color of minimum value of the sparkline.
    max_color : Color
        Color of the maximum value of the sparkline.
    show_tooltip : bool
        Whether to show tooltip.
    tooltip_color_pair : ColorPair
        Color pair for tooltip.
    highlight_color : Color
        Color of highlighted value of the sparkline.
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
        self,
        *,
        data: Sequence[Real] | None = None,
        min_color: Color = DEFAULT_MIN_COLOR,
        max_color: Color = DEFAULT_MAX_COLOR,
        show_tooltip: bool = True,
        tooltip_color_pair: ColorPair = DEFAULT_TOOLTIP_COLORS,
        highlight_color: Color = DEFAULT_HIGHLIGHT_COLOR,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._selector = _BinSelector(
            size=(self.height, 1),
            size_hint=(1.0, None),
            is_enabled=False,
        )
        self.add_widget(self._selector)

        self._tooltip = _Tooltip(size=(7, 18), is_enabled=False)
        self._tooltip.selector = self._selector
        self._tooltip.add_border(style="thick")
        add_text(
            self._tooltip.canvas[1:, 2:],
            "Start:\nStop:\nMin:\nMax:\nMean:",
            italic=True,
        )

        self.tooltip_color_pair = tooltip_color_pair
        self.show_tooltip = show_tooltip
        self.highlight_color = highlight_color
        """Color of highlighted value of the sparkline."""
        self._min_color = min_color
        """Color of minimum value of the sparkline."""
        self._max_color = max_color
        """Color of the maximum value of the sparkline."""
        self.data = data
        # Following are set in `_build_sparkline`:
        self._walls: NDArray[np.float64]
        """
        Boundaries for each bin. The `i`th bin starts at ``self._walls[i]`` and stops at
        ``self._walls[i + 1]``.
        """
        self._mins: NDArray[np.float64]
        """Mininum of each bin."""
        self._maxs: NDArray[np.float64]
        """Maximum of each bin."""
        self._means: NDArray[np.float64]
        """Arithmetic mean of each bin."""

    @property
    def show_tooltip(self) -> bool:
        """Whether to show tooltip."""
        return self._show_tooltip

    @show_tooltip.setter
    def show_tooltip(self, show_tooltip: bool):
        self._show_tooltip = show_tooltip
        self._tooltip.is_enabled = False
        self._selector.is_enabled = False

    @property
    def tooltip_color_pair(self) -> ColorPair:
        """Color pair for tooltip."""
        return self._tooltip.default_color_pair

    @tooltip_color_pair.setter
    def tooltip_color_pair(self, tooltip_color_pair: ColorPair):
        self._tooltip.default_color_pair = tooltip_color_pair
        self._tooltip.colors[:] = tooltip_color_pair

    @property
    def min_color(self) -> Color:
        """Color of minimum value of the sparkline."""
        return self._min_color

    @min_color.setter
    def min_color(self, min_color: Color):
        self._min_color = min_color
        self._build_sparkline()

    @property
    def max_color(self) -> Color:
        """Color of the maximum value of the sparkline."""
        return self._max_color

    @max_color.setter
    def max_color(self, max_color: Color):
        self._max_color = max_color
        self._build_sparkline()

    @property
    def data(self) -> NDArray[np.float64]:
        """Data for the sparkline."""
        return self._data

    @data.setter
    def data(self, data: Sequence[Real] | None):
        self._data = np.array([]) if data is None else np.array(data, float)
        self._build_sparkline()

    def on_add(self):
        self.root.add_widget(self._tooltip)

    def on_remove(self):
        self.root.remove_widget(self._tooltip)

    def on_size(self):
        super().on_size()
        self._build_sparkline()

    def _build_sparkline(self):
        self._selector.is_enabled = False
        self._tooltip.is_enabled = False

        if len(self.data) <= self.width:
            self._walls = np.arange(len(self.data) + 1)
            self._means = self._mins = self._maxs = self.data
            bin_proportions = (self.data - self.data.min(initial=0)) / (
                self.data.max(initial=0) - self.data.min(initial=0)
            )
        else:
            nbins = self.width
            self._walls = np.zeros(nbins + 1, int)
            self._means = np.zeros(nbins)
            self._mins = np.zeros(nbins)
            self._maxs = np.zeros(nbins)
            bin_width = len(self.data) / nbins
            x = 0
            for i in range(nbins):
                start = self._walls[i]
                stop = round(x + bin_width)
                x += bin_width
                self._walls[i + 1] = stop
                self._mins[i] = self.data[start:stop].min()
                self._maxs[i] = self.data[start:stop].max()
                self._means[i] = np.mean(self.data[start:stop])
            bin_proportions = (self._means - self._means.min()) / (
                self._means.max() - self._means.min()
            )

        self.canvas[:] = style_char(self.default_char)
        chars = self.canvas["char"][::-1]
        for i, bin_proportion in enumerate(bin_proportions):
            smooth_bar = create_vertical_bar(self.height, bin_proportion)
            chars[: len(smooth_bar), i] = smooth_bar
            self.colors[:, i, :3] = lerp_colors(
                self.min_color, self.max_color, bin_proportion
            )

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        _, x = self.to_local(mouse_event.position)
        if len(self._means) > x and self.show_tooltip:
            start = f"{self._walls[x]:8d}"
            stop = f"{self._walls[x + 1]:8d}"
            min_ = _get_float_text(self._mins[x])
            max_ = _get_float_text(self._maxs[x])
            mean = _get_float_text(self._means[x])

            add_text(
                self._tooltip.canvas[1:, 8:],
                f"{start}\n{stop}\n{min_}\n{max_}\n{mean}",
            )

            tth, ttw = self._tooltip.size
            my, mx = mouse_event.position
            rh, rw = self.root.size

            if my + tth + 1 < rh:
                tty = my + 1
            elif my - tth - 1 >= 0:
                tty = my - tth - 1
            else:
                tty = 0

            if mx + ttw + 1 < rw:
                ttx = mx + 1
            elif mx - ttw - 1 >= 0:
                ttx = mx - ttw - 1
            else:
                ttx = 0

            self._tooltip.pos = tty, ttx
            self._tooltip.pull_to_front()
            self._tooltip.is_enabled = True

            self._selector.x = x
            self._selector.is_enabled = True

            return True
