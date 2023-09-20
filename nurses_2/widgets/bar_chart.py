from numbers import Real

from wcwidth import wcswidth

from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair, rainbow_gradient
from ..easings import lerp
from ._smooth_bars import create_vertical_bar
from .scroll_view import ScrollView
from .text_widget import TextWidget, add_text
from .widget import Widget

__all__ = ("BarChart",)

TICK_WIDTH = 11
VERTICAL_SPACING = 5
BAR_SPACING = 2
PRECISION = 4
DEFAULT_GRID_COLOR = Color.from_hex("272B40")


class _BarChartProperty:
    def __set_name__(self, owner, name):
        self.name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        setattr(instance, self.name, value)
        instance._build_chart()


class BarChart(Widget):
    """
    A bar chart widget.

    Parameters
    ----------
    data : dict[str, Real]
        Bar chart data.
    min_y : Real | None, default: 0
        Minimum y-value of chart. If `None`, min_y will be minimum of all chart values.
    max_y : Real | None, default: None
        Maximum y-value of chart. If `None`, max_y will be maximum of all chart values.
    bar_colors : list[Color] | None, default: None
        Color of each bar. If `None`, a rainbow gradient is used.
    chart_color_pair : ColorPair, default: DEFAULT_COLOR_THEME.primary
        Color of text in the chart.
    y_label : str | None, default: None
        Optional label for y-axis.
    show_grid_lines : bool, default: True
        Whether to show grid lines.
    grid_line_color : Color, default: DEFAULT_GRID_COLOR
        Color of grid lines if shown.
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
    data : data[str, Real]
        Bar chart data.
    min_y : Real | None
        Minimum y-value of chart. If `None`, min_y will be minimum of all chart values.
    max_y : Real | None
        Maximum y-value of chart. If `None`, max_y will be maximum of all chart values.
    bar_colors : list[Color] | None
        Color of each bar. If `None`, a rainbow gradient is used.
    chart_color_pair : ColorPair
        Color of text in the chart.
    y_label : str | None
        Optional label for y-axis.
    show_grid_lines : bool
        Whether to show grid lines.
    grid_line_color : Color
        Color of grid lines if shown.
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

    data: dict[str, Real] = _BarChartProperty()
    """Data for bar chart."""
    min_y: Real | None = _BarChartProperty()
    """
    Minimum y-value of chart. If `None`, min_y will be minimum of all chart values.
    """
    max_y: Real | None = _BarChartProperty()
    """
    Maximum y-value of chart. If `None`, max_y will be maximum of all chart values.
    """
    bar_colors: list[Color] | None = _BarChartProperty()
    """olor of each bar. If `None`, a rainbow gradient is used."""
    show_grid_lines: bool = _BarChartProperty()
    """Whether to show grid lines."""
    grid_line_color: Color = _BarChartProperty()
    """olor of grid lines if shown."""

    def __init__(
        self,
        data: dict[str, Real],
        *,
        min_y: Real | None = 0,
        max_y: Real | None = None,
        bar_colors: list[Color] | None = None,
        chart_color_pair: ColorPair = DEFAULT_COLOR_THEME.primary,
        y_label: str | None = None,
        show_grid_lines: bool = True,
        grid_line_color: Color = DEFAULT_GRID_COLOR,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._bars = TextWidget()
        self._y_ticks = TextWidget()
        self._y_label_widget = TextWidget()
        self._scrollview = ScrollView(
            show_horizontal_bar=False,
            show_vertical_bar=False,
            allow_vertical_scroll=False,
            disable_ptf=True,
        )
        self._scrollview.view = self._bars

        self.add_widgets(self._scrollview, self._y_ticks, self._y_label_widget)

        self._data = data
        self._min_y = min_y
        self._max_y = max_y
        self._bar_colors = bar_colors
        self._y_label = y_label
        self._show_grid_lines = show_grid_lines
        self._grid_line_color = grid_line_color
        if y_label is not None:
            self._y_label_widget.size = wcswidth(y_label), 1
            add_text(self._y_label_widget.canvas[:, 0], y_label)
        self.chart_color_pair = chart_color_pair

    @property
    def chart_color_pair(self) -> ColorPair:
        """Color of text in the chart."""
        return self._chart_color_pair

    @chart_color_pair.setter
    def chart_color_pair(self, chart_color_pair: ColorPair):
        # Remove any widget transparency
        self.background_char = " "
        self.background_color_pair = chart_color_pair
        self.is_transparent = False

        self._chart_color_pair = chart_color_pair

        for child in self.walk():
            if isinstance(child, TextWidget):
                child.colors[:] = chart_color_pair

        self._build_chart()

    @property
    def y_label(self) -> str | None:
        """Optional label for y-axis."""
        return self._y_label

    @y_label.setter
    def y_label(self, y_label: str | None):
        self._y_label = y_label

        if y_label is not None:
            self._y_label_widget.size = wcswidth(y_label), 1
            add_text(self._y_label_widget.canvas[:, 0], y_label)

        self._build_chart()

    def _build_chart(self):
        h, w = self.size
        has_y_label = self._y_label_widget.is_enabled = bool(self.y_label is not None)

        sv_left = has_y_label + TICK_WIDTH
        sv_width = w - sv_left
        self._scrollview.pos = 0, sv_left
        self._scrollview.size = h, sv_width

        self._y_label_widget.top = h // 2 - self._y_label_widget.height // 2

        nbars = len(self.data)
        min_bar_width = max(map(wcswidth, self.data))
        bars_width = max(
            BAR_SPACING + (min_bar_width + BAR_SPACING) * nbars,
            sv_width,
        )
        bar_width = (bars_width - BAR_SPACING * (nbars + 1)) // nbars
        self._bars.size = h, bars_width
        self._bars.canvas["char"] = " "
        self._bars.colors[:] = self.chart_color_pair

        min_y = min(self.data.values()) if self.min_y is None else self.min_y
        max_y = max(self.data.values()) if self.max_y is None else self.max_y

        canvas_view = self._bars.canvas["char"][::-1]
        colors_view = self._bars.colors[::-1]

        # Regenerate Ticks
        self._y_ticks.size = h, TICK_WIDTH
        self._y_ticks.colors[:] = self.chart_color_pair
        self._y_ticks.left = has_y_label
        self._y_ticks.canvas["char"][0, -1] = "┐"
        self._y_ticks.canvas["char"][1:-2, -1] = "│"
        self._y_ticks.canvas["char"][-2, -1] = "└"

        last_y = h - 3
        for row in range(last_y, -1, -VERTICAL_SPACING):
            y_label = lerp(max_y, min_y, row / last_y)
            self._y_ticks.add_str(
                f"{y_label:>{TICK_WIDTH - 2}.{PRECISION}g} ┤"[:TICK_WIDTH],
                (row, 0),
            )
            if self.show_grid_lines:
                canvas_view[row, :-1] = "─"
                colors_view[row, :, :3] = self.grid_line_color

        bar_colors = (
            rainbow_gradient(nbars) if self.bar_colors is None else self.bar_colors
        )

        y_delta = max_y - min_y

        for i, (label, value) in enumerate(self.data.items()):
            x1 = BAR_SPACING + (bar_width + BAR_SPACING) * i
            x2 = x1 + bar_width
            self._bars.add_str(label.center(bar_width), (h - 1, x1))
            smooth_bar = create_vertical_bar(h - 3, (value - min_y) / y_delta, 0.5)
            canvas_view.T[x1:x2, 2 : 2 + len(smooth_bar)] = smooth_bar
            colors_view[2, x1:x2, :3] = self.chart_color_pair.bg_color
            colors_view[2, x1:x2, 3:] = bar_colors[i]
            colors_view[3 : 2 + len(smooth_bar), x1:x2, :3] = bar_colors[i]
        canvas_view[1, :-1] = "─"
        canvas_view[1, -1] = "┐"

    def on_size(self):
        self._build_chart()
