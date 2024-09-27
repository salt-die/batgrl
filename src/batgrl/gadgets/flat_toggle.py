"""An animated toggle button gadget."""

import asyncio
from collections.abc import Callable, Hashable

from numpy.typing import NDArray

from ..colors import GREEN, Color
from ..text_tools import Cell, smooth_horizontal_bar
from .behaviors.toggle_button_behavior import ToggleButtonBehavior, ToggleState
from .text import Point, PosHint, Size, SizeHint, Text

__all__ = ["FlatToggle", "Point", "Size"]

DARK_GREY = Color.from_hex("222222")
LIGHT_GREY = Color.from_hex("666666")
DARK_RED = Color.from_hex("4f0908")
DARK_GREEN = Color.from_hex("0e4f08")


class FlatToggle(ToggleButtonBehavior, Text):
    r"""
    An animated toggle button gadget.

    Parameters
    ----------
    callback : Callable[ToggleState], None] | None, default: None
        Called when button is released.
    group : Hashable | None, default: None
        If a group is provided, only one button in a group can be in the on state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the off state.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    default_cell : NDArray[Cell] | str, default: " "
        Default cell of text canvas.
    alpha : float, default: 0.0
        Transparency of gadget.
    size : Size, default: Size(1, 3)
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
    callback : Callable[[ToggleState], None] | None
        Called when button is released.
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
    canvas : NDArray[Cell]
        The array of characters for the gadget.
    default_cell : NDArray[Cell]
        Default cell of text canvas.
    default_fg_color : Color
        Foreground color of default cell.
    default_bg_color : Color
        Background color of default cell.
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
    on_toggle()
        Triggled on toggle state change.
    update_off()
        Paint the off state.
    update_on()
        Paint the on state.
    on_release()
        Triggered when a button is released.
    update_normal()
        Paint the normal state.
    update_hover()
        Paint the hover state.
    update_down()
        Paint the down state.
    update_disallowed()
        Paint the disallowed state.
    add_border(style="light", ...)
        Add a border to the gadget.
    add_syntax_highlighting(lexer, style)
        Add syntax highlighting to current text in canvas.
    add_str(str, pos, ...)
        Add a single line of text to the canvas.
    set_text(text, ...)
        Resize gadget to fit text, erase canvas, then fill canvas with text.
    clear()
        Fill canvas with default cell.
    shift(n=1)
        Shift content in canvas up (or down in case of negative `n`).
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
        callback: Callable[[ToggleState], None] | None = None,
        group: None | Hashable = None,
        allow_no_selection: bool = False,
        always_release: bool = False,
        default_cell: NDArray[Cell] | str = " ",
        alpha: float = 0.0,
        size: Size = Size(1, 3),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            group=group,
            allow_no_selection=allow_no_selection,
            always_release=always_release,
            default_cell=default_cell,
            alpha=alpha,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )
        self.callback = callback
        """Called when button is released."""
        self._animation_task: asyncio.Task | None = None
        self._animation_progress: float
        self._animation_progress = float(self.toggle_state == "on")
        self._draw_toggle()

    def _update_color(self):
        if self.button_state == "disallowed":
            on_color = DARK_GREEN
            off_color = DARK_RED
        else:
            on_color = GREEN
            off_color = LIGHT_GREY

        self.canvas["fg_color"] = DARK_GREY
        self.canvas["bg_color"] = on_color if self.toggle_state == "on" else off_color

    def update_off(self):
        """Paint the off state."""
        self._update_color()

    def update_on(self):
        """Paint the on state."""
        self._update_color()

    def update_normal(self):
        """Paint the normal state."""
        self._update_color()

    def update_down(self):
        """Paint the down state."""
        self._update_color()

    def update_hover(self):
        """Paint the hover state."""
        self._update_color()

    def update_disallowed(self):
        """Paint the disallowed state."""
        self._update_color()

    def _draw_toggle(self, _=0.0):
        self.clear()
        self._update_color()

        if self.width < 2:
            return

        x, p = divmod((self.width - 1.25) * self._animation_progress + 0.125, 1)
        x = int(x)
        bar = smooth_horizontal_bar(1, 1, p)
        self.canvas["char"][:, x : x + 2] = bar
        self.canvas["reverse"][:, x] = True

    def on_toggle(self):
        """Animate toggle."""
        if self._animation_task is not None:
            self._animation_task.cancel()
        if self.callback is not None:
            self.callback(self.toggle_state)

        p = float(self.toggle_state == "on")
        self._animation_task = asyncio.create_task(
            self.tween(
                duration=abs(self._animation_progress - p) * 0.3,
                on_progress=self._draw_toggle,
                easing="in_quint",
                _animation_progress=p,
            )
        )

    def on_size(self):
        """Redraw toggle on resize."""
        super().on_size()
        self._draw_toggle()

    def on_remove(self):
        """Stop animation on remove."""
        if self._animation_task is not None:
            self._animation_task.cancel()
        super().on_remove()
