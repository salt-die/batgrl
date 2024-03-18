"""An animated toggle button gadget."""
import asyncio
from collections.abc import Callable, Hashable

from ..colors import BLACK, GREEN, Color
from .behaviors.toggle_button_behavior import (
    ButtonState,
    ToggleButtonBehavior,
    ToggleState,
)
from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text

__all__ = ["FlatToggle", "ToggleState", "ButtonState", "Point", "Size"]

TOGGLE_BLOCK = "▊▋▌▍▎▏"
DARK_GREY = Color.from_hex("222222")
LIGHT_GREY = Color.from_hex("666666")
DARK_RED = Color.from_hex("4f0908")
DARK_GREEN = Color.from_hex("0e4f08")


class _AnimatedToggle(ToggleButtonBehavior, Text):
    def __init__(self, group, allow_no_selection, always_release, bg_color):
        super().__init__(
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            group=group,
            allow_no_selection=allow_no_selection,
            always_release=always_release,
        )
        self._animation_task = None

        if self.toggle_state == "on":
            self.set_text("▄▄▄▄\n█▊▊█\n▀▀▀▀")
            self._animation_progess = 0
        else:
            self.set_text("▄▄▄▄\n█▏▏█\n▀▀▀▀")
            self._animation_progess = 5

        self.canvas["bg_color"] = bg_color
        self.canvas["fg_color"] = DARK_GREY
        self.canvas["bg_color"][1, 1] = DARK_GREY
        if self.toggle_state == "on":
            self.update_on()
        else:
            self.update_off()

    def update_off(self):
        self.canvas["fg_color"][1, 1] = LIGHT_GREY
        self.canvas["bg_color"][1, 2] = LIGHT_GREY

    def update_on(self):
        self.canvas["fg_color"][1, 1] = GREEN
        self.canvas["bg_color"][1, 2] = GREEN

    def update_normal(self):
        if self.toggle_state == "off":
            self.update_off()
        else:
            self.update_on()

    def update_hover(self):
        self.update_normal()

    def update_down(self):
        self.update_normal()

    def update_disallowed(self):
        color = DARK_RED if self.toggle_state == "off" else DARK_GREEN
        self.canvas["fg_color"][1, 1] = color
        self.canvas["bg_color"][1, 2] = color

    async def _animate_toggle(self):
        if self.toggle_state == "on":
            it = range(self._animation_progess - 1, -1, -1)
        else:
            it = range(self._animation_progess + 1, 6)

        for i in it:
            self._animation_progess = i
            self.canvas["char"][1, 1:3] = TOGGLE_BLOCK[i]
            await asyncio.sleep(0.05)

    def on_toggle(self):
        if self._animation_task is not None:
            self._animation_task.cancel()
        if self.parent.callback is not None:
            self.parent.callback(self.toggle_state)
        self._animation_task = asyncio.create_task(self._animate_toggle())

    def on_remove(self):
        if self._animation_task is not None:
            self._animation_task.cancel()


class _ToggleButtonProperty:
    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance._toggle, self.name)

    def __set__(self, instance, value):
        setattr(instance._toggle, self.name, value)


class FlatToggle(Gadget):
    r"""
    An animated toggle button gadget.

    Parameters
    ----------
    callback : Callable[[ToggleState], None] | None, default: None
       Called when button is toggled. The toggle state is provided as first argument.
    toggle_bg_color: Color, default: BLACK
        Background color of toggle.
    group : Hashable | None, default: None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the off state.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
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
    callback : Callable[[ToggleState], None] | None
        Called when button is toggled.
    toggle_background: Color
        Background color of toggle.
    group : Hashable | None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool
        If true and button is in a group, every button can be in the off state.
    toggle_state : ToggleState
        Toggle state of button.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    button_state : ButtonState
        Current button state.
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
    on_size()
        Update gadget after a resize.
    apply_hints()
        Apply size and pos hints.
    to_local(point)
        Convert point in absolute coordinates to local coordinates.
    collides_point(point)
        Return true if point collides with visible portion of gadget.
    collides_gadget(other)
        Return true if other is within gadget's bounding box.
    add_gadget(gadget)
        Add a child gadget.
    add_gadgets(\*gadgets)
        Add multiple child gadgets.
    remove_gadget(gadget)
        Remove a child gadget.
    pull_to_front()
        Move to end of gadget stack so gadget is drawn last.
    walk_from_root()
        Yield all descendents of the root gadget (preorder traversal).
    walk()
        Yield all descendents of this gadget (preorder traversal).
    walk_reverse()
        Yield all descendents of this gadget (reverse postorder traversal).
    ancestors()
        Yield all ancestors of this gadget.
    bind(prop, callback)
        Bind `callback` to a gadget property.
    unbind(uid)
        Unbind a callback from a gadget property.
    on_key(key_event)
        Handle key press event.
    on_mouse(mouse_event)
        Handle mouse event.
    on_paste(paste_event)
        Handle paste event.
    tween(...)
        Sequentially update gadget properties over time.
    on_add()
        Apply size hints and call children's `on_add`.
    on_remove()
        Call children's `on_remove`.
    prolicide()
        Recursively remove all children.
    destroy()
        Remove this gadget and recursively remove all its children.
    """

    group = _ToggleButtonProperty()
    """If a group is provided, only one button in a group can be in the on state."""
    allow_no_selection = _ToggleButtonProperty()
    """If true and button is in a group, every button can be in the off state."""
    toggle_state = _ToggleButtonProperty()
    """Toggle state of button."""
    always_release = _ToggleButtonProperty()
    """Whether a mouse up event outside the button will trigger it."""
    button_state = _ToggleButtonProperty()
    """Current button state."""

    def __init__(
        self,
        *,
        callback: Callable[[ToggleState], None] = None,
        toggle_bg_color: Color = BLACK,
        group: None | Hashable = None,
        allow_no_selection: bool = False,
        always_release: bool = False,
        size: Size = Size(3, 4),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.callback = callback
        self._toggle = _AnimatedToggle(
            group=group,
            allow_no_selection=allow_no_selection,
            always_release=always_release,
            bg_color=toggle_bg_color,
        )
        self.add_gadget(self._toggle)

    @property
    def toggle_bg_color(self) -> Color:
        """Background color of toggle."""
        return Color(*self._toggle.canvas["bg_color"][0, 0])

    @toggle_bg_color.setter
    def toggle_bg_color(self, color: Color):
        self._toggle.canvas["bg_color"][[0, -1]] = color
