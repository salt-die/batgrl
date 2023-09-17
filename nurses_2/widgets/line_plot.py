"""
A 2D line plot widget.
"""
from collections.abc import Sequence
from math import ceil
from numbers import Real
from typing import Literal

import cv2
import numpy as np
from wcwidth import wcswidth

from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair, rainbow_gradient
from ..easings import lerp
from ..io import MouseEvent, MouseEventType
from ._binary_to_char import binary_to_box, binary_to_braille
from .behaviors.movable import Movable
from .scroll_view import ScrollView
from .text_widget import TextWidget, add_text
from .widget import Widget

__all__ = ("LinePlot",)

PLOT_MODES = Literal["braille", "box"]

PLOT_ZOOM = [1.0, 1.25, 1.5, 2.0, 3.0]
TICK_WIDTH = 11
VERTICAL_SPACING = 5
PRECISION = 4

# Derived
TICK_HALF = TICK_WIDTH // 2
VERTICAL_HALF = VERTICAL_SPACING // 2


class _Legend(Movable, TextWidget):
    def _build_legend(self):
        colors = (
            rainbow_gradient(len(self.labels))
            if self.parent.line_colors is None
            else self.parent.line_colors
        )
        self.is_enabled = self.labels and len(self.labels) == len(colors)
        if self.is_enabled:
            height = len(self.labels) + 2
            width = max(map(wcswidth, self.labels)) + 6

            self.size = height, width
            self.colors[:] = self.parent.plot_color_pair
            self.canvas["char"][:] = " "

            self.add_border()

            self.canvas["char"][1:-1, 2] = "█"
            self.colors[1:-1, 2, :3] = colors

            for i, name in enumerate(self.labels, start=1):
                self.add_str(name, (i, 4))


class _LinePlotProperty:
    def __set_name__(self, owner, name):
        self.name = f"_{name}"

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        setattr(instance, self.name, value)
        instance._build_plot()


class LinePlot(Widget):
    """
    A 2D line plot widget.

    Parameters
    ----------
    xs : Sequence[Sequence[Real]]
        x-coordinates of each plot.
    ys : Sequence[Sequence[Real]]
        y-coordinates of each plot.
    mode : Literal["braille", "box"], default: "braille"
        Determines which characters are used to draw the plot.
    min_x : Real | None, default: None
        Minimum x-value of plot. If `None`, min_x will be minimum of all xs.
    max_x : Real | None, default: None
        Maximum x-value of plot. If `None`, max_x will be maximum of all xs.
    min_y : Real | None, default: None
        Minimum y-value of plot. If `None`, min_y will be minimum of all ys.
    max_y : Real | None, default: None
        Maximum y-value of plot. If `None`, max_y will be maximum of all ys.
    line_colors : list[Color] | None, default: None
        The color of each line plot. If `None`, a rainbow gradient is used.
    legend_labels : list[str] | None, default: None
        Labels for legend. If `None`, legend is hidden.
    plot_color_pair : ColorPair, default: DEFAULT_COLOR_THEME.primary,
        Color of text in the plot.
    x_label : str | None, default: None
        Optional label for x-axis.
    y_label : str | None, default: None
        Optional label for y-axis.
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
    xs : Sequence[Sequence[Real]]
        x-coordinates of each plot.
    ys : Sequence[Sequence[Real]]
        y-coordinates of each plot.
    mode : Literal["braille", "box"]
        Determines which characters are used to draw the plot.
    min_x : Real | None
        Minimum x-value of plot. If `None`, min_x will be minimum of all xs.
    max_x : Real | None
        Maximum x-value of plot. If `None`, max_x will be maximum of all xs.
    min_y : Real | None
        Minimum y-value of plot. If `None`, min_y will be minimum of all ys.
    max_y : Real | None
        Maximum y-value of plot. If `None`, max_y will be maximum of all ys.
    line_colors : list[Color] | None
        The color of each line plot. If `None`, a rainbow gradient is used.
    legend_labels : list[str] | None
        Labels for legend. If `None`, legend is hidden.
    plot_color_pair : ColorPair
        Color of text in the plot.
    x_label : str | None
        Optional label for x-axis.
    y_label : str | None
        Optional label for y-axis.
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

    xs: Sequence[Sequence[Real]] = _LinePlotProperty()
    """x-coordinates of each plot."""
    ys: Sequence[Sequence[Real]] = _LinePlotProperty()
    """x-coordinates of each plot."""
    mode: Literal["box", "braille"] = _LinePlotProperty()
    """Determines which characters are used to draw the plot."""
    min_x: Real | None = _LinePlotProperty()
    """Minimum x-value of plot."""
    max_x: Real | None = _LinePlotProperty()
    """Maximum x-value of plot."""
    min_y: Real | None = _LinePlotProperty()
    """Minimum y-value of plot."""
    max_y: Real | None = _LinePlotProperty()
    """Maximum y-value of plot."""
    line_colors: list[Color] | None = _LinePlotProperty()
    """The color of each line plot."""

    def __init__(
        self,
        *,
        xs: Sequence[Sequence[Real]],
        ys: Sequence[Sequence[Real]],
        mode: Literal["box", "braille"] = "braille",
        min_x: Real | None = None,
        max_x: Real | None = None,
        min_y: Real | None = None,
        max_y: Real | None = None,
        line_colors: list[Color] | None = None,
        legend_labels: list[str] | None = None,
        plot_color_pair: ColorPair = DEFAULT_COLOR_THEME.primary,
        x_label: str | None = None,
        y_label: str | None = None,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self._traces_zoom_index = 0
        """Index of size hint in `PLOT_ZOOM` that `_traces` is using."""
        self._traces = TextWidget()
        self._scrollview = ScrollView(
            show_vertical_bar=False,
            show_horizontal_bar=False,
            scrollwheel_enabled=False,
            disable_ptf=True,
        )
        self._scrollview.view = self._traces

        self._x_ticks = TextWidget()

        def set_x_left():
            self._x_ticks.left = (
                self._traces.left + TICK_WIDTH + (self.y_label is not None)
            )

        self._x_ticks.subscribe(self._traces, "pos", set_x_left)

        self._y_ticks = TextWidget()

        def set_y_top():
            self._y_ticks.top = self._traces.top

        self._y_ticks.subscribe(self._traces, "pos", set_y_top)

        self._tick_corner = TextWidget(size=(3, TICK_WIDTH + 1))
        self._tick_corner.canvas["char"][0, -1] = "└"

        self._x_label_widget = TextWidget()
        self._y_label_widget = TextWidget()
        self._legend = _Legend(disable_oob=True, is_enabled=False)
        self._legend.labels = legend_labels

        self.add_widgets(
            self._scrollview,
            self._x_ticks,
            self._y_ticks,
            self._tick_corner,
            self._x_label_widget,
            self._y_label_widget,
            self._legend,
        )

        self._xs = xs
        self._ys = ys
        self._mode = mode
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y
        self._line_colors = line_colors

        self.plot_color_pair = plot_color_pair
        self._x_label = x_label
        if x_label is not None:
            self._x_label_widget.set_text(x_label)
        self.y_label = y_label

    @property
    def plot_color_pair(self) -> ColorPair:
        """Color of text in the plot."""
        return self._plot_color_pair

    @plot_color_pair.setter
    def plot_color_pair(self, plot_color_pair: ColorPair):
        # Remove any widget transparency:
        self.background_char = " "
        self.background_color_pair = plot_color_pair
        self.is_transparent = False

        self._plot_color_pair = plot_color_pair

        for child in self.walk():
            if isinstance(child, TextWidget):
                child.colors[:] = plot_color_pair

        self._legend._build_legend()

    @property
    def legend_labels(self) -> list[str] | None:
        """Labels for legend. If `None`, legend is hidden."""
        return self._legend.labels

    @legend_labels.setter
    def legend_labels(self, legend_labels: list[str] | None):
        self._legend.labels = legend_labels
        self._legend._build_legend()

    @property
    def x_label(self) -> str | None:
        """Optional label for x-axis."""
        return self._x_label

    @x_label.setter
    def x_label(self, x_label: str | None):
        self._x_label = x_label

        if x_label is not None:
            self._x_label_widget.set_text(x_label)

        self._build_plot()

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

        self._build_plot()

    def _build_plot(self):
        h, w = self.size
        has_x_label = self._x_label_widget.is_enabled = bool(self.x_label is not None)
        has_y_label = self._y_label_widget.is_enabled = bool(self.y_label is not None)

        sv_left = has_y_label + TICK_WIDTH
        self._scrollview.pos = 0, sv_left
        self._scrollview.size = h - 2 - has_x_label, w - sv_left

        self._x_label_widget.pos = (
            h - 1,
            self._scrollview.width // 2 - self._x_label_widget.width // 2 + TICK_WIDTH,
        )

        self._y_label_widget.top = (
            self._scrollview.height // 2 - self._y_label_widget.height // 2
        )

        self._legend.top = self._scrollview.height - self._legend.height
        self._legend.left = w - self._legend.width - ceil(TICK_WIDTH / 2)

        zoom = PLOT_ZOOM[self._traces_zoom_index]
        self._traces.size = (
            round(self._scrollview.height * zoom),
            round(self._scrollview.width * zoom),
        )

        offset_h = self._traces.height
        plot_right = self._traces.width - ceil(TICK_WIDTH / 2)
        offset_w = plot_right - TICK_HALF

        if offset_h <= 1 or offset_w <= 1:
            return

        self._traces.canvas["char"][:] = " "
        self._traces.colors[:] = self.plot_color_pair

        min_x = min(xs.min() for xs in self.xs) if self.min_x is None else self.min_x
        max_x = max(xs.max() for xs in self.xs) if self.max_x is None else self.max_x
        min_y = min(ys.min() for ys in self.ys) if self.min_y is None else self.min_y
        max_y = max(ys.max() for ys in self.ys) if self.max_y is None else self.max_y

        canvas_view = self._traces.canvas[:, TICK_HALF:plot_right]
        colors_view = self._traces.colors[:, TICK_HALF:plot_right, :3]

        if self.line_colors is None:
            line_colors = rainbow_gradient(len(self.xs))
        else:
            line_colors = self.line_colors

        x_delta = max_x - min_x
        y_delta = max_y - min_y

        plot_w = offset_w * 2
        if self.mode == "braille":
            plot_h = offset_h * 4
        else:
            plot_h = offset_h * 2

        for xs, ys, color in zip(self.xs, self.ys, line_colors, strict=True):
            plot = np.zeros((plot_h, plot_w), np.uint8)

            scaled_ys = plot_h * (ys - min_y) / y_delta
            scaled_xs = plot_w * (xs - min_x) / x_delta
            coords = np.dstack((scaled_xs, plot_h - scaled_ys)).astype(int)

            cv2.polylines(plot, coords, isClosed=False, color=1)

            if self.mode == "braille":
                sectioned = np.swapaxes(plot.reshape(offset_h, 4, offset_w, 2), 1, 2)
                braille = binary_to_braille(sectioned)
                where_braille = braille != chr(0x2800)  # empty braille character

                canvas_view["char"][where_braille] = braille[where_braille]
                colors_view[where_braille] = color
            else:
                sectioned = np.swapaxes(plot.reshape(offset_h, 2, offset_w, 2), 1, 2)
                boxes = binary_to_box(sectioned)
                where_boxes = boxes != " "
                canvas_view["char"][where_boxes] = boxes[where_boxes]
                colors_view[where_boxes] = color

        # Regenerate Ticks
        self._y_ticks.size = self._traces.height, TICK_WIDTH
        self._y_ticks.colors[:] = self.plot_color_pair
        self._y_ticks.left = has_y_label
        self._y_ticks.canvas["char"][:, :-1] = " "
        self._y_ticks.canvas["char"][1:, -1] = "│"

        self._x_ticks.size = 2, self._traces.width
        self._x_ticks.colors[:] = self.plot_color_pair
        self._x_ticks.top = h - 2 - has_x_label
        self._x_ticks.canvas["char"][0, : plot_right - 1] = "─"
        self._x_ticks.canvas["char"][0, plot_right:] = " "
        self._x_ticks.canvas["char"][1:] = " "

        self._tick_corner.pos = h - 2 - has_x_label, sv_left - TICK_WIDTH - 1

        last_y = offset_h - 1
        for row in range(last_y, -1, -VERTICAL_SPACING):
            y_label = lerp(max_y, min_y, row / last_y)
            self._y_ticks.add_str(
                f"{y_label:>{TICK_WIDTH - 2}.{PRECISION}g} ┤"[:TICK_WIDTH],
                (row, 0),
            )
        self._y_ticks.canvas["char"][0, -1] = "┐"

        last_x = offset_w - 1
        for column in range(0, offset_w, TICK_WIDTH):
            x_label = lerp(min_x, max_x, column / last_x)
            self._x_ticks.canvas["char"][0, column + TICK_HALF] = "┬"
            self._x_ticks.add_str(
                f"{x_label:^{TICK_WIDTH}.{PRECISION}g}"[:TICK_WIDTH],
                (1, column),
            )
        self._x_ticks.canvas["char"][0, plot_right - 1] = "┐"

    def on_size(self):
        self._build_plot()

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        if mouse_event.event_type is MouseEventType.SCROLL_UP:
            if self._traces_zoom_index >= len(PLOT_ZOOM) - 1:
                return True
            self._traces_zoom_index += 1
        elif mouse_event.event_type is MouseEventType.SCROLL_DOWN:
            if self._traces_zoom_index <= 0:
                return True
            self._traces_zoom_index -= 1
        else:
            return super().on_mouse(mouse_event)

        self._build_plot()
        return True
