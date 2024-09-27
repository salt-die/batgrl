"""A sparkline gadget."""

from collections.abc import Sequence
from numbers import Real

import numpy as np
from numpy.typing import NDArray

from ..colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG, Color, lerp_colors
from ..terminal.events import MouseEvent
from ..text_tools import smooth_vertical_bar
from ._cursor import Cursor
from .gadget import Gadget, Point, PosHint, Size, SizeHint
from .text import Text, add_text

__all__ = ["Sparkline", "Point", "Size"]

DEFAULT_MIN_COLOR = Color.from_hex("1b244b")
DEFAULT_MAX_COLOR = Color.from_hex("4d67ff")
DEFAULT_HIGHLIGHT_COLOR = Color.from_hex("7281ff")


def _get_float_text(value: float) -> str:
    text = f"{value:8.2f}"
    if len(text) > 8:
        return f"{value:3.2e}"
    return text


class _Tooltip(Text):
    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self.is_enabled = self.selector.is_enabled = False


class Sparkline(Gadget):
    r"""
    A sparkline gadget for displaying sequential data.

    Parameters
    ----------
    data : Sequence[Real] | None, default: None
        Data for the sparkline.
    min_color : Color, default: DEFAULT_MIN_COLOR
        Color of minimum value of the sparkline.
    max_color : Color, default: DEFAULT_MAX_COLOR
        Color of the maximum value of the sparkline.
    highlight_color : Color, default: DEFAULT_HIGHLIGHT_COLOR
        Color of highlighted value of the sparkline.
    bg_color : Color, default: DEFAULT_PRIMARY_BG
        Background color of gadget.
    show_tooltip : bool, default: True
        Whether to show tooltip.
    tooltip_fg_color : Color, default: DEFAULT_PRIMARY_FG
        Foreground color of tooltip.
    tooltip_bg_color : Color, default: DEFAULT_PRIMARY_BG
        Background color of tooltip.
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
    data : NDArray[np.float64]
        Data for the sparkline. This can be set with a `Sequence[Real]` or `None`, but
        will be converted into a (possibly empty) numpy array.
    min_color : Color
        Color of minimum value of the sparkline.
    max_color : Color
        Color of the maximum value of the sparkline.
    highlight_color : Color
        Color of highlighted value of the sparkline.
    bg_color : Color
        Background color of gadget.
    show_tooltip : bool
        Whether to show tooltip.
    tooltip_fg_color : Color
        Foreground color of tooltip.
    tooltip_bg_color : Color
        Background color of tooltip.
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

    def __init__(
        self,
        *,
        data: Sequence[Real] | None = None,
        min_color: Color = DEFAULT_MIN_COLOR,
        max_color: Color = DEFAULT_MAX_COLOR,
        highlight_color: Color = DEFAULT_HIGHLIGHT_COLOR,
        bg_color: Color = DEFAULT_PRIMARY_BG,
        show_tooltip: bool = True,
        tooltip_fg_color: Color = DEFAULT_PRIMARY_FG,
        tooltip_bg_color: Color = DEFAULT_PRIMARY_BG,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._sparkline = Text(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self._selector = Cursor(size_hint={"height_hint": 1.0})
        self._tooltip = _Tooltip(size=(7, 18), is_enabled=False)

        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self._tooltip.selector = self._selector
        self._tooltip.add_border(style="thick")
        add_text(
            self._tooltip.canvas[1:, 2:],
            "*Start:*\n*Stop:*\n*Min:*\n*Max:*\n*Mean:*",
            markdown=True,
        )
        self.add_gadget(self._sparkline)
        self._sparkline.add_gadget(self._selector)

        self.data = data
        self._min_color = min_color
        """Color of minimum value of the sparkline."""
        self._max_color = max_color
        """Color of the maximum value of the sparkline."""
        self.highlight_color = highlight_color
        self.bg_color = bg_color
        self.show_tooltip = show_tooltip
        self.tooltip_fg_color = tooltip_fg_color
        self.tooltip_bg_color = tooltip_bg_color

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
    def bg_color(self) -> Color:
        """Background color of gadget."""
        return self._selector.bg_color

    @bg_color.setter
    def bg_color(self, bg_color: Color):
        self._selector.bg_color = bg_color
        self._sparkline.default_bg_color = bg_color
        self._sparkline.canvas["bg_color"] = bg_color

    @property
    def highlight_color(self) -> Color:
        """Color of highlighted value of the sparkline."""
        return self._selector.fg_color

    @highlight_color.setter
    def highlight_color(self, highlight_color: Color):
        self._selector.fg_color = highlight_color

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
    def tooltip_fg_color(self) -> Color:
        """Foreground color of tooltip."""
        return self._tooltip.default_fg_color

    @tooltip_fg_color.setter
    def tooltip_fg_color(self, tooltip_fg_color: Color):
        self._tooltip.default_fg_color = tooltip_fg_color
        self._tooltip.canvas["fg_color"] = tooltip_fg_color

    @property
    def tooltip_bg_color(self) -> Color:
        """Background color of tooltip."""
        return self._tooltip.default_bg_color

    @tooltip_bg_color.setter
    def tooltip_bg_color(self, tooltip_bg_color: Color):
        self._tooltip.default_bg_color = tooltip_bg_color
        self._tooltip.canvas["bg_color"] = tooltip_bg_color

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
        """Add tooltip to root and build sparkline on add."""
        super().on_add()
        self.root.add_gadget(self._tooltip)
        self._build_sparkline()

    def on_remove(self):
        """Remove tooltip from root on remove."""
        self.root.remove_gadget(self._tooltip)

    def on_size(self):
        """Rebuild sparkline on resize."""
        super().on_size()
        self._build_sparkline()

    def _build_sparkline(self):
        if not self.root:
            return

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

        self._sparkline.clear()
        chars = self._sparkline.canvas["char"][::-1]
        fg_color = self._sparkline.canvas["fg_color"]
        for i, bin_proportion in enumerate(bin_proportions):
            smooth_bar = smooth_vertical_bar(self.height, bin_proportion)
            chars[: len(smooth_bar), i] = smooth_bar
            fg_color[:, i] = lerp_colors(self.min_color, self.max_color, bin_proportion)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        """Show tooltip and highlight column on mouse collision."""
        if not self.collides_point(mouse_event.pos):
            return

        _, x = self.to_local(mouse_event.pos)
        if self.show_tooltip and len(self._means) > x:
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
            my, mx = mouse_event.pos
            rh, rw = self.root.size

            # Keep the tooltip inbounds:
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
