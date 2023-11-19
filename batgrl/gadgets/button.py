"""A button gadget."""
from collections.abc import Callable

from numpy.typing import NDArray
from wcwidth import wcswidth

from ..colors import ColorPair
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
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
from .text import Text

__all__ = [
    "Button",
    "ButtonState",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]


class Button(Themable, ButtonBehavior, Gadget):
    r"""
    A button gadget.

    Parameters
    ----------
    label : str, default: ""
        Button label.
    callback : Callable[[], None], default: lambda: None
        Called when button is released.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    background_char : NDArray[Char] | str | None, default: " "
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
    label : str
        Button label.
    callback : Callable[[], None]
        Called when button is released.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of `NORMAL`, `HOVER`, `DOWN`.
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
    update_theme():
        Paint the gadget with current theme.
    update_normal():
        Paint the normal state.
    update_hover():
        Paint the hover state.
    update_down():
        Paint the down state.
    on_release():
        Triggered when a button is released.
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
        label: str = "",
        callback: Callable[[], None] = lambda: None,
        always_release: bool = False,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: NDArray[Char] | str | None = " ",
        background_color_pair: ColorPair | None = None,
    ):
        self._label_gadget = Text(pos_hint={"y_hint": 0.5, "x_hint": 0.5})

        super().__init__(
            always_release=always_release,
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

        self.add_gadget(self._label_gadget)

        self.label = label
        self.callback = callback

    def update_theme(self):
        """Paint the gadget with current theme."""
        match self.state:
            case ButtonState.NORMAL:
                self.update_normal()
            case ButtonState.HOVER:
                self.update_hover()
            case ButtonState.DOWN:
                self.update_down()

    @property
    def label(self) -> str:
        """Button label."""
        return self._label

    @label.setter
    def label(self, label: str):
        self._label = label
        self._label_gadget.size = 1, wcswidth(label)
        self._label_gadget.apply_hints()
        self._label_gadget.add_str(label)

    def update_normal(self):
        """Paint the normal state."""
        self.background_color_pair = self._label_gadget.colors[
            :
        ] = self.color_theme.button_normal

    def update_hover(self):
        """Paint the hover state."""
        self.background_color_pair = self._label_gadget.colors[
            :
        ] = self.color_theme.button_hover

    def update_down(self):
        """Paint the down state."""
        self.background_color_pair = self._label_gadget.colors[
            :
        ] = self.color_theme.button_press

    def on_release(self):
        """Triggered when button is released."""
        self.callback()
