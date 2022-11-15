"""
A 2D line plot widget.
"""
import numpy as np

from wcwidth import wcswidth

from ...colors import Color, WHITE_ON_BLACK
from ...io import MouseEvent, MouseEventType
from ..text_widget import TextWidget, SizeHint, Anchor, Size
from ..scroll_view import ScrollView
from ..widget import Widget
from ._legend import _Legend
from ._traces import _Traces, TICK_WIDTH, TICK_HALF

PLOT_SIZES = [SizeHint(x, x) for x in (1.0, 1.25, 1.75, 2.75, 5.0)]


class LinePlot(Widget):
    """
    A 2D line plot widget.

    Parameters
    ----------
    *points : list[float] | numpy.ndarray
        The horizontal / vertical coordinates of the data points.
        For `n` plots, there should be `2 * n` 1D arrays.
    xmin : float | None, default: None
        Minimum x-value of plot. If None, xmin will be minimum of all xs.
    xmax : float | None, default: None
        Maximum x-value of plot. If None, xmax will be maximum of all xs.
    ymin : float | None, default: None
        Minimum y-value of plot. If None, ymin will be minimum of all ys.
    ymax : float | None, default: None
        Maximum y-value of plot. If None, ymax will be maximum of all ys.
    xlabel : str | None, default: None
        Optional label for x-axis.
    ylabel : str | None, default: None
        Optional label for y-axis.
    legend_labels : list[str] | None, default: None
        If provided, a moveable legend will be added for each plot.
    line_colors : list[Color] | None, default: None
        The color of each line plot. A rainbow gradient is used as default.
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
        *points: list[float] | np.ndarray,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        xlabel: str | None=None,
        ylabel: str | None=None,
        legend_labels: list[str] | None=None,
        line_colors: list[Color] | None=None,
        background_char=" ",
        **kwargs,
    ):
        super().__init__(background_char=background_char, **kwargs)

        self._trace_size_hint = 0

        self.plot = Widget(
            is_transparent=self.is_transparent,
            background_char=self.background_char,
            background_color_pair=self.background_color_pair,
        )

        text_kwargs = dict(
            is_transparent=self.is_transparent,
            default_char=self.background_char or " ",
            default_color_pair=self.background_color_pair or WHITE_ON_BLACK,
        )

        self._traces = _Traces(
            *points,
            xmin=xmin,
            xmax=xmax,
            ymin=ymin,
            ymax=ymax,
            line_colors=line_colors,
            **text_kwargs
        )

        self._scrollview = ScrollView(
            pos=(0, TICK_WIDTH),
            show_vertical_bar=False,
            show_horizontal_bar=False,
            scrollwheel_enabled=False,
        )
        self._scrollview.view = self._traces

        self._tick_corner = TextWidget(
            size=(2, TICK_WIDTH),
            pos_hint=(1.0, None),
            anchor=Anchor.BOTTOM_LEFT,
            **text_kwargs
        )
        self._tick_corner.canvas[0, -1] = "└"

        self.plot.add_widgets(
            self._scrollview,
            self._traces.x_ticks,
            self._traces.y_ticks,
            self._tick_corner,
        )

        self.add_widget(self.plot)

        if xlabel is not None:
            self.xlabel = TextWidget(size=(1, wcswidth(xlabel)), **text_kwargs)
            self.xlabel.add_text(xlabel)
            self.add_widget(self.xlabel)
        else:
            self.xlabel = None

        if ylabel is not None:
            self.ylabel = TextWidget(size=(wcswidth(ylabel), 1), **text_kwargs)
            self.ylabel.get_view[:, 0].add_text(ylabel)
            self.plot.left += 1
            self.add_widget(self.ylabel)
        else:
            self.ylabel = None

        if legend_labels is not None:
            if len(legend_labels) != len(self._traces.all_xs):
                raise ValueError("number of labels inconsistent with number of plots")

            self.legend = _Legend(
                legend_labels,
                self._traces.line_colors,
                **text_kwargs
            )
            self.add_widget(self.legend)
        else:
            self.legend = None

    def on_size(self):
        h, w = self._size

        xlabel = self.xlabel
        ylabel = self.ylabel

        has_xlabel = bool(xlabel)
        has_ylabel = bool(ylabel)

        plot = self.plot
        plot.size = max(1, h - has_xlabel), max(1, w - has_ylabel)

        scrollview = self._scrollview
        scrollview.size = max(1, plot.height - 2), max(1, plot.width - TICK_WIDTH)

        hint_y, hint_x = PLOT_SIZES[self._trace_size_hint]
        self._traces.size = round(scrollview.height * hint_y), round(scrollview.width * hint_x)

        if has_xlabel:
            xlabel.pos = h - 1, scrollview.width // 2 - xlabel.width // 2 + TICK_WIDTH + has_ylabel

        if has_ylabel:
            ylabel.top = scrollview.height // 2 - ylabel.height // 2

        if self.legend:
            legend = self.legend
            legend.top = h - legend.height - 3
            legend.left = w - legend.width - TICK_HALF - TICK_WIDTH % 2

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        match mouse_event.event_type:
            case MouseEventType.SCROLL_UP:
                self._trace_size_hint = min(self._trace_size_hint + 1, len(PLOT_SIZES) - 1)
            case MouseEventType.SCROLL_DOWN:
                self._trace_size_hint = max(0, self._trace_size_hint - 1)
            case _:
                return super().on_mouse(mouse_event)

        self._traces.size_hint = PLOT_SIZES[self._trace_size_hint]
        return True
