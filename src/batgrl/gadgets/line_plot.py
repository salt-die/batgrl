"""A 2-D line plot gadget."""

from __future__ import annotations

from collections.abc import Sequence
from math import ceil
from numbers import Real
from typing import Literal

import cv2
import numpy as np

from ..colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG, Color, rainbow_gradient
from ..terminal.events import MouseEvent
from ..text_tools import binary_to_box, binary_to_braille, str_width
from .behaviors.movable import Movable
from .gadget import Gadget, Point, PosHint, Size, SizeHint, lerp
from .pane import Pane
from .scroll_view import ScrollView
from .text import Text, add_text, new_cell

__all__ = ["LinePlot", "Point", "Size"]

PLOT_ZOOM = [1.0, 1.25, 1.5, 2.0, 3.0]
TICK_WIDTH = 11
VERTICAL_SPACING = 5
PRECISION = 4

# Derived
TICK_HALF = TICK_WIDTH // 2
VERTICAL_HALF = VERTICAL_SPACING // 2


class _Legend(Movable, Text):
    def _build_legend(self):
        plot: LinePlot = self.parent.parent
        colors = (
            rainbow_gradient(len(self.labels))
            if plot.line_colors is None
            else plot.line_colors
        )
        self.is_enabled = self.labels and len(self.labels) == len(colors)
        if self.is_enabled:
            height = len(self.labels) + 2
            width = max(map(str_width, self.labels)) + 6

            self.size = height, width
            self.canvas["fg_color"] = plot.plot_fg_color
            self.canvas["bg_color"] = plot.plot_bg_color
            self.canvas["char"][:] = " "

            self.add_border()

            self.canvas["char"][1:-1, 2] = "█"
            self.canvas["fg_color"][1:-1, 2] = colors

            for i, name in enumerate(self.labels, start=1):
                self.add_str(name, pos=(i, 4))


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


class LinePlot(Gadget):
    r"""
    A 2-D line plot gadget.

    Zoom in or out with mouse wheel or "page_up"/"page_down".

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
    plot_fg_color : Color, default: DEFAULT_PRIMARY_FG,
        Foreground color of the plot.
    plot_bg_color : Color, default: DEFAULT_PRIMARY_BG,
        Background color of the plot.
    x_label : str | None, default: None
        Optional label for x-axis.
    y_label : str | None, default: None
        Optional label for y-axis.
    alpha : float, default: 1.0
        Transparency of gadget.
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
    plot_fg_color : Color
        Foreground color of the plot.
    plot_bg_color : Color
        Background color of the plot.
    x_label : str | None
        Optional label for x-axis.
    y_label : str | None
        Optional label for y-axis.
    alpha : float
        Transparency of gadget.
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
        plot_fg_color: Color = DEFAULT_PRIMARY_FG,
        plot_bg_color: Color = DEFAULT_PRIMARY_BG,
        x_label: str | None = None,
        y_label: str | None = None,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        default_cell = new_cell(fg_color=plot_fg_color, bg_color=plot_bg_color)
        self._traces = Text(default_cell=default_cell)
        self._scroll_view = ScrollView(
            show_vertical_bar=False,
            show_horizontal_bar=False,
            scrollwheel_enabled=False,
            alpha=0,
        )
        self._x_ticks = Text(default_cell=default_cell)
        self._y_ticks = Text(default_cell=default_cell)
        self._x_ticks_container = Gadget(is_transparent=True)
        self._y_ticks_container = Gadget(is_transparent=True)
        self._tick_corner = Text(size=(3, TICK_WIDTH + 1), default_cell=default_cell)
        self._x_label_gadget = Text(default_cell=default_cell)
        self._y_label_gadget = Text(default_cell=default_cell)
        self._legend = _Legend(disable_oob=True, is_enabled=False)
        self._container = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, bg_color=plot_bg_color
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

        self._xs = xs
        self._ys = ys
        self._mode = mode
        self._min_x = min_x
        self._max_x = max_x
        self._min_y = min_y
        self._max_y = max_y
        self._line_colors = line_colors
        self._legend.labels = legend_labels
        self._plot_fg_color = plot_fg_color
        self._plot_bg_color = plot_bg_color
        self.alpha = alpha
        self.on_transparency()
        self.x_label = x_label
        self.y_label = y_label
        self._traces_zoom_index = 0
        """Index of size hint in `PLOT_ZOOM` that `_traces` is using."""

        def set_x_left():
            self._x_ticks.left = self._traces.left

        def set_y_top():
            self._y_ticks.top = self._traces.top

        self._traces.bind("pos", set_x_left)
        self._traces.bind("pos", set_y_top)
        self._tick_corner.canvas["char"][0, -1] = "└"

        self._scroll_view.view = self._traces
        self._x_ticks_container.add_gadget(self._x_ticks)
        self._y_ticks_container.add_gadget(self._y_ticks)
        self._container.add_gadgets(
            self._scroll_view,
            self._x_ticks_container,
            self._y_ticks_container,
            self._tick_corner,
            self._x_label_gadget,
            self._y_label_gadget,
            self._legend,
        )
        self.add_gadget(self._container)
        self._legend._build_legend()

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self._traces.is_transparent = self.is_transparent
        self._scroll_view.is_transparent = self.is_transparent
        self._x_ticks.is_transparent = self.is_transparent
        self._y_ticks.is_transparent = self.is_transparent
        self._tick_corner.is_transparent = self.is_transparent
        self._x_label_gadget.is_transparent = self.is_transparent
        self._y_label_gadget.is_transparent = self.is_transparent
        self._container.is_transparent = self.is_transparent

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._container.alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._container.alpha = alpha

    @property
    def plot_fg_color(self) -> Color:
        """Foreground color of text in the plot."""
        return self._plot_fg_color

    @plot_fg_color.setter
    def plot_fg_color(self, plot_fg_color: Color):
        self._plot_fg_color = plot_fg_color

        for child in self.walk():
            if isinstance(child, Text):
                child.canvas["fg_color"] = plot_fg_color
                child.default_fg_color = plot_fg_color
            elif isinstance(child, Pane):
                child.fg_color = plot_fg_color

        self._legend._build_legend()

    @property
    def plot_bg_color(self) -> Color:
        """Foreground color of text in the plot."""
        return self._plot_bg_color

    @plot_bg_color.setter
    def plot_bg_color(self, plot_bg_color: Color):
        self._plot_bg_color = plot_bg_color

        for child in self.walk():
            if isinstance(child, Text):
                child.canvas["bg_color"] = plot_bg_color
                child.default_bg_color = plot_bg_color
            elif isinstance(child, Pane):
                child.bg_color = plot_bg_color

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
            self._x_label_gadget.set_text(x_label)

        self._build_plot()

    @property
    def y_label(self) -> str | None:
        """Optional label for y-axis."""
        return self._y_label

    @y_label.setter
    def y_label(self, y_label: str | None):
        self._y_label = y_label

        if y_label is not None:
            self._y_label_gadget.size = str_width(y_label), 1
            add_text(self._y_label_gadget.canvas[:, 0], y_label)

        self._build_plot()

    def _build_plot(self):
        h, w = self.size
        if self.root is None or h == 0 or w == 0:
            return

        has_x_label = self._x_label_gadget.is_enabled = self.x_label is not None
        has_y_label = self._y_label_gadget.is_enabled = self.y_label is not None

        sv_left = has_y_label + TICK_WIDTH
        self._scroll_view.pos = 0, sv_left
        self._scroll_view.size = h - 2 - has_x_label, w - sv_left
        self._y_ticks_container.left = has_y_label
        self._y_ticks_container.size = self._scroll_view.height, TICK_WIDTH
        self._x_ticks_container.top = self._scroll_view.bottom
        self._x_ticks_container.left = self._y_ticks_container.right
        self._x_ticks_container.size = 2, self._scroll_view.width

        self._x_label_gadget.pos = (
            h - 1,
            self._scroll_view.width // 2 - self._x_label_gadget.width // 2 + TICK_WIDTH,
        )

        self._y_label_gadget.top = (
            self._scroll_view.height // 2 - self._y_label_gadget.height // 2
        )

        self._legend.top = self._scroll_view.height - self._legend.height
        self._legend.left = w - self._legend.width - ceil(TICK_WIDTH / 2)

        zoom = PLOT_ZOOM[self._traces_zoom_index]
        self._traces.size = (
            round(self._scroll_view.height * zoom),
            round(self._scroll_view.width * zoom),
        )

        offset_h = self._traces.height
        plot_right = self._traces.width - ceil(TICK_WIDTH / 2)
        offset_w = plot_right - TICK_HALF

        if offset_h <= 1 or offset_w <= 1:
            return

        self._traces.canvas["char"][:] = " "
        self._traces.canvas["fg_color"] = self.plot_fg_color
        self._traces.canvas["bg_color"] = self.plot_bg_color

        min_x = min(xs.min() for xs in self.xs) if self.min_x is None else self.min_x
        max_x = max(xs.max() for xs in self.xs) if self.max_x is None else self.max_x
        min_y = min(ys.min() for ys in self.ys) if self.min_y is None else self.min_y
        max_y = max(ys.max() for ys in self.ys) if self.max_y is None else self.max_y

        chars_view = self._traces.canvas["char"][:, TICK_HALF:plot_right]
        colors_view = self._traces.canvas["fg_color"][:, TICK_HALF:plot_right]

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

                chars_view[where_braille] = braille[where_braille]
                colors_view[where_braille] = color
            else:
                sectioned = np.swapaxes(plot.reshape(offset_h, 2, offset_w, 2), 1, 2)
                boxes = binary_to_box(sectioned)
                where_boxes = boxes != " "
                chars_view[where_boxes] = boxes[where_boxes]
                colors_view[where_boxes] = color

        # Regenerate Ticks
        self._y_ticks.size = self._traces.height, TICK_WIDTH
        self._y_ticks.canvas["fg_color"] = self.plot_fg_color
        self._y_ticks.canvas["bg_color"] = self.plot_bg_color
        self._y_ticks.canvas["char"][:, :-1] = " "
        self._y_ticks.canvas["char"][1:, -1] = "│"

        self._x_ticks.size = 2, self._traces.width
        self._x_ticks.canvas["fg_color"] = self.plot_fg_color
        self._x_ticks.canvas["bg_color"] = self.plot_bg_color
        self._x_ticks.canvas["char"][0, : plot_right - 1] = "─"
        self._x_ticks.canvas["char"][0, plot_right:] = " "
        self._x_ticks.canvas["char"][1:] = " "

        self._tick_corner.pos = h - 2 - has_x_label, sv_left - TICK_WIDTH - 1

        last_y = offset_h - 1
        for row in range(last_y, -1, -VERTICAL_SPACING):
            y_label = lerp(max_y, min_y, row / last_y)
            self._y_ticks.add_str(
                f"{y_label:>{TICK_WIDTH - 2}.{PRECISION}g} ┤"[:TICK_WIDTH],
                pos=(row, 0),
            )
        self._y_ticks.canvas["char"][0, -1] = "┐"

        last_x = offset_w - 1
        for column in range(0, offset_w, TICK_WIDTH):
            x_label = lerp(min_x, max_x, column / last_x)
            self._x_ticks.canvas["char"][0, column + TICK_HALF] = "┬"
            self._x_ticks.add_str(
                f"{x_label:^{TICK_WIDTH}.{PRECISION}g}"[:TICK_WIDTH],
                pos=(1, column),
            )
        self._x_ticks.canvas["char"][0, plot_right - 1] = "┐"

    def on_size(self):
        """Rebuild plot on resize."""
        self._build_plot()

    def _zoom_in(self):
        if self._traces_zoom_index < len(PLOT_ZOOM) - 1:
            self._traces_zoom_index += 1

    def _zoom_out(self):
        if self._traces_zoom_index > 0:
            self._traces_zoom_index -= 1

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """Zoom-in or -out on mouse wheel."""
        if not self.collides_point(mouse_event.pos):
            return

        if mouse_event.event_type == "scroll_up":
            self._zoom_in()
        elif mouse_event.event_type == "scroll_down":
            self._zoom_out()
        else:
            return super().on_mouse(mouse_event)

        self._build_plot()
        return True

    def on_key(self, key_event):
        """Zoom-in or -out with "page_up" or "page_down"."""
        if key_event.key == "page_up":
            self._zoom_in()
        elif key_event.key == "page_down":
            self._zoom_out()
        else:
            return super().on_key(key_event)

        self._build_plot()
        return True

    def on_add(self):
        """Built plot on add."""
        super().on_add()
        self._build_plot()
