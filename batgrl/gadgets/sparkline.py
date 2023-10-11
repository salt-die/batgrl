from collections.abc import Sequence
from numbers import Real

import numpy as np
from numpy.typing import NDArray

from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair, lerp_colors
from ..io import MouseEvent
from .gadget import Gadget
from .text import (
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    Text,
    add_text,
    style_char,
)
from .text_tools import smooth_vertical_bar

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Sparkline",
]

DEFAULT_TOOLTIP_COLORS = DEFAULT_COLOR_THEME.primary
DEFAULT_MIN_COLOR = Color.from_hex("1B244B")
DEFAULT_MAX_COLOR = Color.from_hex("4D67FF")
DEFAULT_HIGHLIGHT_COLOR = Color.from_hex("7281FF")


def _get_float_text(value: float) -> str:
    text = f"{value:8.2f}"
    if len(text) > 8:
        return f"{value:3.2e}"
    return text


class _Tooltip(Text):
    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self.is_enabled = self.selector.is_enabled = False


class Sparkline(Text):
    """
    A sparkline gadget for displaying sequential data.

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
    default_color_pair : ColorPair, default: DEFAULT_COLOR_THEME.primary
        Default color of gadget.
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
        The array of characters for the gadget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in :attr:`canvas`.
    default_char : str
        Default background character.
    default_color_pair : ColorPair
        Default color pair of gadget.
    default_fg_color : Color
        The default foreground color.
    default_bg_color : Color
        The default background color.
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
    add_border:
        Add a border to the gadget.
    add_str:
        Add a single line of text to the canvas.
    set_text:
        Resize gadget to fit text, erase canvas, then fill canvas with text.
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

    def __init__(
        self,
        *,
        data: Sequence[Real] | None = None,
        min_color: Color = DEFAULT_MIN_COLOR,
        max_color: Color = DEFAULT_MAX_COLOR,
        show_tooltip: bool = True,
        tooltip_color_pair: ColorPair = DEFAULT_TOOLTIP_COLORS,
        highlight_color: Color = DEFAULT_HIGHLIGHT_COLOR,
        default_char: str = " ",
        default_color_pair: ColorPair = DEFAULT_COLOR_THEME.primary,
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
            default_char=default_char,
            default_color_pair=default_color_pair,
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

        self._selector = Gadget(
            size=(self.height, 1),
            size_hint={"height_hint": 1.0},
            is_enabled=False,
            is_transparent=True,
        )
        self.add_gadget(self._selector)

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
    def highlight_color(self) -> Color:
        """Color of highlighted value of the sparkline."""
        return self._highlight_color

    @highlight_color.setter
    def highlight_color(self, highlight_color: Color):
        self._highlight_color = highlight_color
        self._selector.background_color_pair = ColorPair.from_colors(
            highlight_color, self.default_bg_color
        )

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
        self.root.add_gadget(self._tooltip)

    def on_remove(self):
        self.root.remove_gadget(self._tooltip)

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
            smooth_bar = smooth_vertical_bar(self.height, bin_proportion)
            chars[: len(smooth_bar), i] = smooth_bar
            self.colors[:, i, :3] = lerp_colors(
                self.min_color, self.max_color, bin_proportion
            )

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if not self.collides_point(mouse_event.position):
            return

        _, x = self.to_local(mouse_event.position)
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