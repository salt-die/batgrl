"""An animated toggle button gadget."""
import asyncio
from collections.abc import Callable, Hashable

from numpy.typing import NDArray

from ..colors import BLACK, GREEN, Color, ColorPair
from .behaviors.toggle_button_behavior import (
    ButtonState,
    ToggleButtonBehavior,
    ToggleState,
)
from .gadget import (
    Char,
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
)
from .text import Text, add_text

__all__ = [
    "ButtonState",
    "FlatToggle",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "ToggleState",
]

TOGGLE_BLOCK = "▊▋▌▍▎▏"
DARK_GREY = Color.from_hex("333333")
LIGHT_GREY = Color.from_hex("666666")


class _AnimatedToggle(ToggleButtonBehavior, Text):
    def __init__(
        self, group, allow_no_selection, toggle_state, always_release, bg_color
    ):
        super().__init__(
            size=(3, 4),
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            group=group,
            allow_no_selection=allow_no_selection,
            toggle_state=toggle_state,
            always_release=always_release,
        )
        self._animation_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

        self.colors[..., 3:] = bg_color
        self.colors[..., :3] = DARK_GREY
        self.colors[1, 1, 3:] = DARK_GREY

        if self.toggle_state is ToggleState.ON:
            add_text(self.canvas, "▄▄▄▄\n█▊▊█\n▀▀▀▀")
            self.colors[1, 1, :3] = GREEN
            self.colors[1, 2, 3:] = GREEN
            self._animation_progess = 0
        else:
            add_text(self.canvas, "▄▄▄▄\n█▏▏█\n▀▀▀▀")
            self.colors[1, 1, :3] = LIGHT_GREY
            self.colors[1, 2, 3:] = LIGHT_GREY
            self._animation_progess = 5

    def on_remove(self):
        self._animation_task.cancel()

    async def _animate_toggle(self):
        if self.toggle_state is ToggleState.ON:
            self.colors[1, 1, :3] = GREEN
            self.colors[1, 2, 3:] = GREEN
            r = range(self._animation_progess - 1, -1, -1)
        else:
            self.colors[1, 1, :3] = LIGHT_GREY
            self.colors[1, 2, 3:] = LIGHT_GREY
            r = range(self._animation_progess + 1, 6)

        for i in r:
            self._animation_progess = i
            self.canvas["char"][1, 1:3] = TOGGLE_BLOCK[i]
            await asyncio.sleep(0.05)

        self.parent.callback(self.toggle_state)

    def on_toggle(self):
        if not hasattr(self, "_animation_task"):
            # Initializing...
            return
        self._animation_task.cancel()
        self._animation_task = asyncio.create_task(self._animate_toggle())


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
    callback : Callable[[ToggleState], None], default: lambda state: None
        Called when toggle state changes. The new state is provided as first argument.
    toggle_background_color: Color, default: BLACK
        Background color of toggle.
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
        size : Size, default: Size(10, 10)
        Size of gadget.
    background_char : NDArray[Char] | str | None, default: None
        The background character of the gadget. If not given and not transparent, the
        background characters of the root gadget are painted. If not given and
        transparent, characters behind the gadget are visible. The character must be
        single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the gadget. If not given and not transparent, the
        background color pair of the root gadget is painted. If not given and
        transparent, the color pairs behind the gadget are visible.
    size : Size, default: Size(10, 10)
        Size of gadget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        A transparent gadget allows regions beneath it to be painted.
    is_visible : bool, default: True
        Whether gadget is visible. Gadget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether gadget is enabled. A disabled gadget is not painted and doesn't receive
        input events.

    Attributes
    ----------
    callback : Callable[[ToggleState], None]
        Toggle button callback.
    toggle_background: Color
        Background color of toggle.
    background_char : NDArray[Char] | None
        The background character of the gadget.
    background_color_pair : ColorPair | None
        The background color pair of the gadget.
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

    group = _ToggleButtonProperty()
    """If a group is provided, only one button in a group can be in the on state."""
    allow_no_selection = _ToggleButtonProperty()
    """If true and button is in a group, every button can be in the off state."""
    toggle_state = _ToggleButtonProperty()
    """Toggle state of button."""
    always_release = _ToggleButtonProperty()
    """Whether a mouse up event outside the button will trigger it."""

    def __init__(
        self,
        *,
        size: Size = Size(3, 4),
        callback: Callable[[ToggleState], None] = lambda state: None,
        toggle_background_color: Color = BLACK,
        group: None | Hashable = None,
        allow_no_selection: bool = False,
        toggle_state: ToggleState = ToggleState.OFF,
        always_release: bool = False,
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: NDArray[Char] | str | None = None,
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

        self.callback = callback

        self._toggle = _AnimatedToggle(
            group=group,
            allow_no_selection=allow_no_selection,
            toggle_state=toggle_state,
            always_release=always_release,
            bg_color=toggle_background_color,
        )
        self.add_gadget(self._toggle)

    @property
    def toggle_background_color(self) -> Color:
        """Background color of toggle."""
        return Color(*self._toggle[0, 0, 3:])

    @toggle_background_color.setter
    def toggle_background_color(self, color: Color):
        self._toggle.colors[[0, -1], :, 3:] = color
