from numbers import Real

from wcwidth import wcswidth

from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair, rainbow_gradient
from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    lerp,
)
from .scroll_view import ScrollView
from .text import Text, add_text
from .text_tools import smooth_vertical_bar

__all__ = [
    "BarChart",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

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
        instance.build_chart()


class BarChart(Gadget):
    """
    A bar chart gadget.

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
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the gadget if the gadget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget if the gadget is not transparent.

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
        Size of gadget.
    height : int
        Height of gadget.
    rows : int
        Alias for :attr:`height`.
    width : int
        Width of gadget.
    columns : int
        Alias for :attr:`width`.
    pos : Point
        Position of upper-left corner.
    top : int
        Y-coordinate of top of gadget.
    y : int
        Y-coordinate of top of gadget.
    left : int
        X-coordinate of left side of gadget.
    x : int
        X-coordinate of left side of gadget.
    bottom : int
        Y-coordinate of bottom of gadget.
    right : int
        X-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the gadget if the gadget is not transparent.
    background_color_pair : ColorPair | None
        Background color pair.
    parent : Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        True if gadget is transparent.
    is_visible : bool
        True if gadget is visible.
    is_enabled : bool
        True if gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    build_chart:
        Build bar chart and set canvas and color arrays.
    on_size:
        Called when gadget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of gadget.
    collides_gadget:
        True if other is within gadget's bounding box.
    add_gadget:
        Add a child gadget.
    add_gadgets:
        Add multiple child gadgets.
    remove_gadget:
        Remove a child gadget.
    pull_to_front:
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root:
        Yield all descendents of root gadget.
    walk:
        Yield all descendents (or ancestors if `reverse` is true).
    subscribe:
        Subscribe to a gadget property.
    unsubscribe:
        Unsubscribe to a gadget property.
    on_key:
        Handle key press event.
    on_mouse:
        Handle mouse event.
    on_paste:
        Handle paste event.
    tween:
        Sequentially update a gadget property over time.
    on_add:
        Called after a gadget is added to gadget tree.
    on_remove:
        Called before gadget is removed from gadget tree.
    prolicide:
        Recursively remove all children.
    destroy:
        Destroy this gadget and all descendents.
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

        self._bars = Text()
        self._y_ticks = Text()
        self._y_label_gadget = Text()
        self._scrollview = ScrollView(
            show_horizontal_bar=False,
            show_vertical_bar=False,
            allow_vertical_scroll=False,
            disable_ptf=True,
        )
        self._scrollview.view = self._bars

        self.add_gadgets(self._scrollview, self._y_ticks, self._y_label_gadget)

        self._data = data
        self._min_y = min_y
        self._max_y = max_y
        self._bar_colors = bar_colors
        self._y_label = y_label
        self._show_grid_lines = show_grid_lines
        self._grid_line_color = grid_line_color
        if y_label is not None:
            self._y_label_gadget.size = wcswidth(y_label), 1
            add_text(self._y_label_gadget.canvas[:, 0], y_label)
        self.chart_color_pair = chart_color_pair

    @property
    def chart_color_pair(self) -> ColorPair:
        """Color of text in the chart."""
        return self._chart_color_pair

    @chart_color_pair.setter
    def chart_color_pair(self, chart_color_pair: ColorPair):
        # Remove any gadget transparency
        self.background_char = " "
        self.background_color_pair = chart_color_pair
        self.is_transparent = False

        self._chart_color_pair = chart_color_pair

        for child in self.walk():
            if isinstance(child, Text):
                child.colors[:] = chart_color_pair

        self.build_chart()

    @property
    def y_label(self) -> str | None:
        """Optional label for y-axis."""
        return self._y_label

    @y_label.setter
    def y_label(self, y_label: str | None):
        self._y_label = y_label

        if y_label is not None:
            self._y_label_gadget.size = wcswidth(y_label), 1
            add_text(self._y_label_gadget.canvas[:, 0], y_label)

        self.build_chart()

    def build_chart(self):
        """
        Build bar chart and set canvas and color arrays.
        """
        h, w = self.size
        has_y_label = self._y_label_gadget.is_enabled = bool(self.y_label is not None)

        sv_left = has_y_label + TICK_WIDTH
        sv_width = w - sv_left
        self._scrollview.pos = 0, sv_left
        self._scrollview.size = h, sv_width

        self._y_label_gadget.top = h // 2 - self._y_label_gadget.height // 2

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
            smooth_bar = smooth_vertical_bar(h - 3, (value - min_y) / y_delta, 0.5)
            canvas_view.T[x1:x2, 2 : 2 + len(smooth_bar)] = smooth_bar
            colors_view[2, x1:x2, :3] = self.chart_color_pair.bg_color
            colors_view[2, x1:x2, 3:] = bar_colors[i]
            colors_view[3 : 2 + len(smooth_bar), x1:x2, :3] = bar_colors[i]
        canvas_view[1, :-1] = "─"
        canvas_view[1, -1] = "┐"

    def on_size(self):
        self.build_chart()