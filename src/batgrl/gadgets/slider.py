"""A slider gadget."""

from collections.abc import Callable

from ..colors import BLACK, WHITE, Color
from ..terminal.events import MouseButton, MouseEvent
from .behaviors.grabbable import Grabbable
from .pane import Pane, Point, PosHint, Size, SizeHint, bindable, clamp
from .text import Text

__all__ = ["Slider", "Point", "Size"]


class Slider(Grabbable, Pane):
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
    handle_color : Color, default: WHITE
        Color of handle.
    slider_color: Color, default: WHITE
        Color of slider.
    fill_color: Color, default: WHITE
        Color of filled portion of slider.
    slider_enabled : bool, default: True
        Whether slider value can be changed.
    is_grabbable : bool, default: True
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool, default: False
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton, default: "left"
        Mouse button used for grabbing.
    bg_color : Color, default: BLACK
        Background color of gadget.
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
    min : float
        Minimum value of slider.
    max : float
        Maximum value of slider.
    value : float
        Current value of slider.
    callback : Callable
        Single argument callable called with new value of slider when slider is updated.
    slider_color: Color
        Color of slider.
    fill_color: Color
        Color of filled portion of slider.
    fill_color: Color
        Color of filled portion of slider.
    slider_enabled : bool
        Whether slider value can be changed.
    proportion : float
        Current proportion of slider.
    is_grabbable : bool
        Whether grabbable behavior is enabled.
    ptf_on_grab : bool
        Whether the gadget will be pulled to front when grabbed.
    mouse_button : MouseButton
        Mouse button used for grabbing.
    bg_color : Color
        Background color of gadget.
    alpha : float
        Transparency of gadget.
    is_grabbed : bool
        Whether gadget is grabbed.
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
    grab(mouse_event)
        Grab the gadget.
    ungrab(mouse_event)
        Ungrab the gadget.
    grab_update(mouse_event)
        Update gadget with incoming mouse events while grabbed.
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
        min: float,
        max: float,
        start_value: float | None = None,
        callback: Callable | None = None,
        handle_color: Color = WHITE,
        slider_color: Color = WHITE,
        fill_color: Color = WHITE,
        slider_enabled: bool = True,
        is_grabbable: bool = True,
        ptf_on_grab: bool = False,
        mouse_button: MouseButton = "left",
        bg_color: Color = BLACK,
        alpha: float = 1.0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            ptf_on_grab=ptf_on_grab,
            mouse_button=mouse_button,
            bg_color=bg_color,
            alpha=alpha,
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

        self._slider = Text(
            default_cell="━",
            size=(1, 1),
            pos_hint={"y_hint": 0.5, "anchor": "top"},
            size_hint={"width_hint": 1.0},
            is_transparent=True,
        )
        self._handle = Text(
            default_cell="█", size=(1, 1), pos_hint={"y_hint": 0.5, "anchor": "top"}
        )
        self.add_gadgets(self._slider, self._handle)

        self.handle_color = handle_color
        self.slider_color = slider_color
        self.fill_color = fill_color
        self.callback = callback
        self.slider_enabled = slider_enabled
        self.value = self.min if start_value is None else start_value

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
    def handle_color(self) -> Color:
        """Color of handle."""
        return self._handle.default_fg_color

    @handle_color.setter
    def handle_color(self, handle_color: Color | str):
        self._handle.default_fg_color = handle_color
        self._handle.canvas["fg_color"] = handle_color

    @property
    def slider_color(self) -> Color:
        """Color of slider."""
        return self._slider.default_fg_color

    @slider_color.setter
    def slider_color(self, slider_color: Color | str):
        self._slider.default_fg_color = slider_color
        self._slider.canvas["fg_color"][:, self._handle.x :] = slider_color

    @property
    def fill_color(self) -> Color:
        """Color of "filled" portion of slider."""
        return self._fill_color

    @fill_color.setter
    def fill_color(self, color: Color):
        self._fill_color = color
        self._slider.canvas["fg_color"][:, : self._handle.x] = color

    @property
    def proportion(self) -> float:
        """Current proportion of slider."""
        return self._proportion

    @proportion.setter
    @bindable
    def proportion(self, value: float):
        if not self.slider_enabled:
            return

        self._proportion = clamp(value, 0, 1)
        self._value = (self.max - self.min) * self._proportion + self.min

        self._handle.x = x = round(self._proportion * self.fill_width)
        self._slider.canvas["fg_color"][:, :x] = self.fill_color
        self._slider.canvas["fg_color"][:, x:] = self.slider_color

        if self.callback is not None:
            self.callback(self._value)

    @property
    def value(self) -> float:
        """Current value of slider."""
        return self._value

    @value.setter
    @bindable
    def value(self, value: float):
        value = clamp(value, self.min, self.max)
        self.proportion = (value - self.min) / (self.max - self.min)

    @property
    def fill_width(self):
        """Width of the slider minus the width of the handle."""
        return self.width - self._handle.width

    def on_size(self):
        """Resize canvas and color arrays and reposition slider handle."""
        super().on_size()
        self.proportion = self.proportion

    def on_add(self):
        """Resize canvas and color arrays and reposition slider handle."""
        super().on_add()
        self.proportion = self.proportion

    def grab(self, mouse_event: MouseEvent):
        """Move handle to mouse position on grab."""
        if (
            mouse_event.event_type == "mouse_down"
            and self.collides_point(mouse_event.pos)
            and self.to_local(mouse_event.pos).y == self.height // 2
        ):
            super().grab(mouse_event)
            self.grab_update(mouse_event)

    def grab_update(self, mouse_event: MouseEvent):
        """Update proportion and handle position on grab update."""
        x = clamp(self.to_local(mouse_event.pos).x, 0, self.fill_width)
        self.proportion = 0 if self.fill_width == 0 else x / self.fill_width
