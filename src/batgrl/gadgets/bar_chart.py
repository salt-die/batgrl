"""A bar chart gadget."""

from numbers import Real

from ..colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG, Color, rainbow_gradient
from ..text_tools import add_text, smooth_vertical_bar, str_width
from .gadget import Gadget, Point, PosHint, Size, SizeHint, lerp
from .pane import Pane
from .scroll_view import ScrollView
from .text import Text, new_cell

__all__ = ["BarChart", "Point", "Size"]

TICK_WIDTH = 11
VERTICAL_SPACING = 5
BAR_SPACING = 2
PRECISION = 4
DEFAULT_GRID_COLOR = Color.from_hex("272b40")


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


class BarChart(Gadget):
    r"""
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
    chart_fg_color: Color, default: DEFAULT_PRIMARY_FG
        Foreground color of chart.
    chart_bg_color: Color, default: DEFAULT_PRIMARY_BG
        Background color of chart.
    alpha: float, default: 1.0
        Transparency of gadget.
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
    size_hint : SizeHint | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | None, default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether gadget is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

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
    chart_fg_color: Color
        Foreground color of chart.
    chart_bg_color: Color
        Background color of chart.
    alpha: float
        Transparency of gadget.
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
        y-coordinate of top of gadget.
    y : int
        y-coordinate of top of gadget.
    left : int
        x-coordinate of left side of gadget.
    x : int
        x-coordinate of left side of gadget.
    bottom : int
        y-coordinate of bottom of gadget.
    right : int
        x-coordinate of right side of gadget.
    center : Point
        Position of center of gadget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    parent: Gadget | None
        Parent gadget.
    children : list[Gadget]
        Children gadgets.
    is_transparent : bool
        Whether gadget is transparent.
    is_visible : bool
        Whether gadget is visible.
    is_enabled : bool
        Whether gadget is enabled.
    root : Gadget | None
        If gadget is in gadget tree, return the root gadget.
    app : App
        The running app.

    Methods
    -------
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    tween(...)
        Sequentially update gadget properties over time.
    on_size()
        Update gadget after a resize.
    on_transparency()
        Update gadget after transparency is enabled/disabled.
    on_add()
        Update gadget after being added to the gadget tree.
    on_remove()
        Update gadget after being removed from the gadget tree.
    on_key(key_event)
        Handle a key press event.
    on_mouse(mouse_event)
        Handle a mouse event.
    on_paste(paste_event)
        Handle a paste event.
    on_terminal_focus(focus_event)
        Handle a focus event.
    """

    data: dict[str, Real] = _BarChartProperty()
    """Data for bar chart."""
    min_y: Real | None = _BarChartProperty()
    """Minimum y-value of chart. If `None`, min_y will be minimum of chart values."""
    max_y: Real | None = _BarChartProperty()
    """Maximum y-value of chart. If `None`, max_y will be maximum of chart values."""
    bar_colors: list[Color] | None = _BarChartProperty()
    """Color of each bar. If `None`, a rainbow gradient is used."""
    chart_fg_color: Color = _BarChartProperty()
    """Foreground color of bar chart."""
    chart_bg_color: Color = _BarChartProperty()
    """Background color of bar chart."""
    alpha: float = _BarChartProperty()
    """Transparency of gadget."""
    y_label: str = _BarChartProperty()
    """Optional label for y-axis."""
    show_grid_lines: bool = _BarChartProperty()
    """Whether to show grid lines."""
    grid_line_color: Color = _BarChartProperty()
    """Color of grid lines if shown."""

    def __init__(
        self,
        data: dict[str, Real],
        *,
        min_y: Real | None = 0,
        max_y: Real | None = None,
        bar_colors: list[Color] | None = None,
        chart_fg_color: Color = DEFAULT_PRIMARY_FG,
        chart_bg_color: Color = DEFAULT_PRIMARY_BG,
        alpha: float = 1.0,
        y_label: str | None = None,
        show_grid_lines: bool = True,
        grid_line_color: Color = DEFAULT_GRID_COLOR,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._bars = Text(is_transparent=is_transparent)
        self._scroll_view = ScrollView(
            show_horizontal_bar=False,
            show_vertical_bar=False,
            allow_vertical_scroll=False,
            alpha=0,
            is_transparent=is_transparent,
        )
        self._scroll_view.view = self._bars
        self._y_ticks = Text(is_transparent=is_transparent)
        self._y_label_gadget = Text(is_transparent=is_transparent)
        self._container = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            is_transparent=is_transparent,
        )
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self._container.add_gadgets(
            self._scroll_view, self._y_ticks, self._y_label_gadget
        )
        self.add_gadget(self._container)

        self.data = data
        self.min_y = min_y
        self.max_y = max_y
        self.bar_colors = bar_colors
        self.chart_fg_color = chart_fg_color
        self.chart_bg_color = chart_bg_color
        self.alpha = alpha
        self.y_label = y_label
        self.show_grid_lines = show_grid_lines
        self.grid_line_color = grid_line_color

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._container.is_transparent = self.is_transparent
        self._y_ticks.is_transparent = self.is_transparent
        self._y_label_gadget.is_transparent = self.is_transparent
        self._scroll_view.is_transparent = self.is_transparent
        self._bars.is_transparent = self.is_transparent

    def on_add(self):
        """Build chart on add."""
        super().on_add()
        self._build_chart()

    def _build_chart(self):
        """Build bar chart and set canvas and color arrays."""
        if not self.root:
            return

        self._container.bg_color = self.chart_bg_color
        self._container.alpha = self.alpha

        h, w = self.size
        has_y_label = self._y_label_gadget.is_enabled = self.y_label is not None
        if has_y_label:
            self._y_label_gadget.size = str_width(self.y_label), 1
            self._y_label_gadget.top = h // 2 - self._y_label_gadget.height // 2
            add_text(
                self._y_label_gadget.canvas[:, 0],
                self.y_label,
                fg_color=self.chart_fg_color,
                bg_color=self.chart_bg_color,
            )

        sv_left = has_y_label + TICK_WIDTH
        sv_width = w - sv_left
        self._scroll_view.pos = 0, sv_left
        self._scroll_view.size = h, sv_width

        nbars = len(self.data)
        min_bar_width = max(map(str_width, self.data))
        bars_width = max(
            BAR_SPACING + (min_bar_width + BAR_SPACING) * nbars,
            sv_width,
        )
        bar_width = (bars_width - BAR_SPACING * (nbars + 1)) // nbars
        self._bars.size = h, bars_width
        self._bars.canvas[:] = new_cell(
            fg_color=self.chart_fg_color, bg_color=self.chart_bg_color
        )

        min_y = min(self.data.values()) if self.min_y is None else self.min_y
        max_y = max(self.data.values()) if self.max_y is None else self.max_y

        chars = self._bars.canvas["char"][::-1]
        fg_colors = self._bars.canvas["fg_color"][::-1]

        # Regenerate Ticks
        self._y_ticks.left = has_y_label
        self._y_ticks.size = h, TICK_WIDTH
        self._y_ticks.canvas["fg_color"] = self.chart_fg_color
        self._y_ticks.canvas["bg_color"] = self.chart_bg_color
        self._y_ticks.canvas["char"][0, -1] = "┐"
        self._y_ticks.canvas["char"][1:-2, -1] = "│"
        self._y_ticks.canvas["char"][-2, -1] = "└"

        last_y = h - 3
        for row in range(last_y, -1, -VERTICAL_SPACING):
            y_label = lerp(max_y, min_y, row / last_y)
            self._y_ticks.add_str(
                f"{y_label:>{TICK_WIDTH - 2}.{PRECISION}g} ┤"[:TICK_WIDTH],
                pos=(row, 0),
            )
            if self.show_grid_lines:
                chars[row, :-1] = "─"
                fg_colors[row] = self.grid_line_color

        bar_colors = self.bar_colors or rainbow_gradient(nbars)
        y_delta = max_y - min_y

        for i, (label, value) in enumerate(self.data.items()):
            x1 = BAR_SPACING + (bar_width + BAR_SPACING) * i
            x2 = x1 + bar_width
            self._bars.add_str(label.center(bar_width), pos=(h - 1, x1))
            smooth_bar = smooth_vertical_bar(h - 3, (value - min_y) / y_delta, 0.5)
            chars.T[x1:x2, 2 : 2 + len(smooth_bar)] = smooth_bar
            fg_colors[2 : 2 + len(smooth_bar), x1:x2] = bar_colors[i]
            self._bars.canvas["reverse"][::-1].T[x1:x2, 2] = True
        chars[1, :-1] = "─"
        chars[1, -1] = "┐"

    def on_size(self):
        """Rebuild bar chart."""
        self._build_chart()
