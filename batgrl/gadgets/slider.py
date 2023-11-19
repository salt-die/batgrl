"""A slider gadget."""
from collections.abc import Callable

from numpy.typing import NDArray

from ..colors import Color, ColorPair
from ..io import MouseButton, MouseEvent, MouseEventType
from .behaviors.grabbable import Grabbable
from .text import (
    Char,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    Text,
    clamp,
    coerce_char,
    style_char,
    subscribable,
)

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "Slider",
]

DEFAULT_SLIDER_COLOR_PAIR = ColorPair.from_hex("2A3CA0070C25")
DEFAULT_SLIDER_FILL_COLOR = Color.from_hex("5A6FE8")
DEFAULT_SLIDER_HANDLE_COLOR_PAIR = ColorPair.from_hex("DDE4ED070C25")


class Slider(Grabbable, Text):
    r"""
    A slider gadget.

    Parameters
    ----------
    min : float
        Minimum value of slider.
    max : float
        Maximum value of slider.
    start_value: float | None, default: None
        Start value of slider. If `None`, start value is :attr:`min`.
    callback : Callable | None, default: None
        Single argument callable called with new value of slider when slider is updated.
    handle_color_pair : ColorPair | None, default: DEFAULT_SLIDER_HANDLE_COLOR_PAIR
        Color pair of slider handle. If `None`, handle color pair is
        :attr:`default_color_pair`.
    handle_char : NDArray[Char] | str, default: "█"
        Character used for slider handle.
    fill_color: Color | None, default: DEFAULT_SLIDER_FILL_COLOR
        Color of "filled" portion of slider. If `None`, fill color is
        :attr:`default_color_pair`.
    fill_char: NDArray[Char] | str, default: "▬"
        Character used for slider.
    slider_enabled : bool, default: True
        Whether slider value can be changed.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
    default_char : NDArray[Char] | str, default: " "
        Default background character. This should be a single unicode half-width
        grapheme.
    default_color_pair : ColorPair, default: DEFAULT_SLIDER_COLOR_PAIR
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
        Whether whitespace is transparent.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    min : float
        Minimum value of slider.
    max : float
        Maximum value of slider.
    value : float
        Current value of slider.
    callback : Callable
        Single argument callable called with new value of slider when slider is updated.
    handle_color_pair : ColorPair
        Color pair of slider handle.
    handle_char : NDArray[Char]
        Character used for slider handle.
    fill_color : Color
        Color of "filled" portion of slider.
    fill_char : NDArray[Char]
        Character used for slider.
    slider_enabled : bool
        True if slider value can be changed.
    proportion : float
        Current proportion of slider.
    is_grabbable : bool
        If false, grabbable behavior is disabled.
    disable_ptf : bool
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    is_grabbed : bool
        True if gadget is grabbed.
    mouse_dyx : Point
        Last change in mouse position.
    mouse_dy : int
        Last vertical change in mouse position.
    mouse_dx : int
        Last horizontal change in mouse position.
    canvas : NDArray[Char]
        The array of characters for the gadget.
    colors : NDArray[np.uint8]
        The array of color pairs for each character in `canvas`.
    default_char : NDArray[Char]
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
    parent: GadgetBase | None
        Parent gadget.
    children : list[GadgetBase]
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
    grab(mouse_event):
        Grab the gadget.
    ungrab(mouse_event):
        Ungrab the gadget.
    grab_update(mouse_event):
        Update gadget with incoming mouse events while grabbed.
    add_border(style="light", ...):
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style):
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...):
        Add a single line of text to the canvas.
    set_text(text, ...):
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    on_size():
        Update gadget after a resize.
    apply_hints():
        Apply size and pos hints.
    to_local(point):
        Convert point in absolute coordinates to local coordinates.
    collides_point(point):
        Return true if point collides with visible portion of gadget.
    collides_gadget(other):
        Return true if other is within gadget's bounding box.
    add_gadget(gadget):
        Add a child gadget.
    add_gadgets(\*gadgets):
        Add multiple child gadgets.
    remove_gadget(gadget):
        Remove a child gadget.
    pull_to_front():
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root():
        Yield all descendents of the root gadget (preorder traversal).
    walk():
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse():
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors():
        Yield all ancestors of this gadget.
    subscribe(source, attr, action):
        Subscribe to a gadget property.
    unsubscribe(source, attr):
        Unsubscribe to a gadget property.
    on_key(key_event):
        Handle key press event.
    on_mouse(mouse_event):
        Handle mouse event.
    on_paste(paste_event):
        Handle paste event.
    tween(...):
        Sequentially update gadget properties over time.
    on_add():
        Apply size hints and call children's `on_add`.
    on_remove():
        Call children's `on_remove`.
    prolicide():
        Recursively remove all children.
    destroy():
        Remove this gadget and recursively remove all its children.
    """

    def __init__(
        self,
        *,
        min: float,
        max: float,
        start_value: float | None = None,
        callback: Callable | None = None,
        handle_color_pair: ColorPair | None = DEFAULT_SLIDER_HANDLE_COLOR_PAIR,
        handle_char: NDArray[Char] | str = "█",
        fill_color: Color | None = DEFAULT_SLIDER_FILL_COLOR,
        fill_char: NDArray[Char] | str = "▬",
        slider_enabled: bool = True,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
        default_char: NDArray[Char] | str = " ",
        default_color_pair: ColorPair = DEFAULT_SLIDER_COLOR_PAIR,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            disable_ptf=disable_ptf,
            mouse_button=mouse_button,
            default_char=default_char,
            default_color_pair=default_color_pair,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        if min >= max:
            raise ValueError(f"{min=} >= {max=}")
        self._min = min
        self._max = max

        self._handle = Text(size=(1, 1), pos_hint={"y_hint": 0.5, "anchor": "top"})
        self.add_gadget(self._handle)
        self.handle_color_pair = handle_color_pair or self.default_color_pair
        self.handle_char = handle_char

        self.fill_color = fill_color or self.default_fg_color
        self.fill_char = fill_char

        self.callback = callback

        self.slider_enabled = True
        self.value = self.min if start_value is None else start_value
        self.slider_enabled = slider_enabled

    @property
    def min(self) -> float:
        """Minimum value of slider."""
        return self._min

    @min.setter
    def min(self, value: float):
        if value >= self.max:
            raise ValueError("Min can't be greater than or equal to max.")

        self._min = value
        self.proportion = self.proportion

    @property
    def max(self) -> float:
        """Maximum value of slider."""
        return self._max

    @max.setter
    def max(self, value: float):
        if value <= self.min:
            raise ValueError("Max can't be less than or equal to min.")

        self._max = value
        self.proportion = self.proportion

    @property
    def handle_color_pair(self) -> ColorPair:
        """Color pair of slider handle."""
        return self._handle_color_pair

    @handle_color_pair.setter
    def handle_color_pair(self, color_pair: ColorPair):
        self._handle_color_pair = color_pair
        self._handle.colors[:] = color_pair

    @property
    def handle_char(self) -> NDArray[Char]:
        """Character used for slider handle."""
        return self._handle_char

    @handle_char.setter
    def handle_char(self, char: NDArray[Char] | str):
        self._handle_char = coerce_char(char, style_char("█"))
        self._handle.canvas[:] = char

    @property
    def fill_color(self) -> Color:
        """Color of "filled" portion of slider."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color: Color):
        self._fill_color = color
        self.colors[self.height // 2, :, :3] = color

    @property
    def fill_char(self) -> NDArray[Char]:
        """Character used for slider."""
        return self._fill_char

    @fill_char.setter
    def fill_char(self, char: NDArray[Char] | str):
        self._fill_char = coerce_char(char, style_char("▬"))
        self.canvas[self.height // 2] = self._fill_char

    def on_size(self):
        """Resize canvas and color arrays and reposition slider handle."""
        super().on_size()
        self.canvas[:] = self.default_char
        self.canvas[self.height // 2] = self.fill_char
        self.colors[:] = self.default_color_pair
        self.proportion = self.proportion

    @property
    def proportion(self) -> float:
        """Current proportion of slider."""
        return self._proportion

    @proportion.setter
    @subscribable
    def proportion(self, value: float):
        if not self.slider_enabled:
            return

        self._proportion = clamp(value, 0, 1)
        self._value = (self.max - self.min) * self._proportion + self.min

        self._handle.x = x = round(self._proportion * self.fill_width)
        y = self.height // 2
        self.colors[y, :x, :3] = self.fill_color
        self.colors[y, x:, :3] = self.default_fg_color

        if self.callback is not None:
            self.callback(self._value)

    @property
    def value(self) -> float:
        """Current value of slider."""
        return self._value

    @value.setter
    @subscribable
    def value(self, value: float):
        value = clamp(value, self.min, self.max)
        self.proportion = (value - self.min) / (self.max - self.min)

    @property
    def fill_width(self):
        """Width of the slider minus the width of the handle."""
        return self.width - self._handle.width

    def grab(self, mouse_event: MouseEvent):
        """Move handle to mouse position on grab."""
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_point(mouse_event.position)
            and self.to_local(mouse_event.position).y == self.height // 2
        ):
            super().grab(mouse_event)
            self.grab_update(mouse_event)

    def grab_update(self, mouse_event: MouseEvent):
        """Update proportion and handle position on grab update."""
        x = clamp(self.to_local(mouse_event.position).x, 0, self.width - 1)
        self._handle.x = x
        self.proportion = 0 if self.fill_width == 0 else x / self.fill_width
