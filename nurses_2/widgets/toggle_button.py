"""
A toggle button widget.
"""
from collections.abc import Callable, Hashable

from wcwidth import wcswidth

from ..colors import ColorPair
from .behaviors.themable import Themable
from .behaviors.toggle_button_behavior import (
    ButtonState,
    ToggleButtonBehavior,
    ToggleState,
)
from .text_widget import TextWidget
from .widget import Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict, Widget

__all__ = [
    "ButtonState",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "ToggleButton",
    "ToggleState",
]

CHECK_OFF = "□ "
CHECK_ON = "▣ "
TOGGLE_OFF = "◯ "
TOGGLE_ON = "◉ "


class ToggleButton(Themable, ToggleButtonBehavior, Widget):
    """
    A toggle button widget. Without a group, a toggle button acts like a checkbox.
    With a group it behaves like a radio button (only a single button in a group is
    allowed to be in the "on" state).

    Parameters
    ----------
    label : str, default: ""
        Toggle button label.
    callback : Callable[[ToggleState], None], default: lambda: None
        Called when toggle state changes. The new state is provided as first argument.
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button. If button is in a group and
        :attr:`allow_no_selection` is false this value will be ignored if all buttons
        would be "off".
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint | SizeHintDict | None, default: None
        Size as a proportion of parent's height and width.
    pos_hint : PosHint | PosHintDict | None , default: None
        Position as a proportion of parent's height and width.
    is_transparent : bool, default: False
        Whether :attr:`background_char` and :attr:`background_color_pair` are painted.
    is_visible : bool, default: True
        Whether widget is visible. Widget will still receive input events if not
        visible.
    is_enabled : bool, default: True
        Whether widget is enabled. A disabled widget is not painted and doesn't receive
        input events.
    background_char : str | None, default: None
        The background character of the widget if the widget is not transparent.
        Character must be single unicode half-width grapheme.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if the widget is not transparent.

    Attributes
    ----------
    label : str
        Toggle button label.
    callback : Callable[[ToggleState], None]
        Button callback when toggled.
    group : None | Hashable
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool
        If true and button is in a group, every button can be in the "off" state.
    toggle_state : ToggleState
        Toggle state of button.
    always_release : bool
        Whether a mouse up event outside the button will trigger it.
    state : ButtonState
        Current button state. One of `NORMAL`, `HOVER`, `DOWN`.
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
        Position of upper-left corner.
    top : int
        Y-coordinate of top of widget.
    y : int
        Y-coordinate of top of widget.
    left : int
        X-coordinate of left side of widget.
    x : int
        X-coordinate of left side of widget.
    bottom : int
        Y-coordinate of bottom of widget.
    right : int
        X-coordinate of right side of widget.
    center : Point
        Position of center of widget.
    absolute_pos : Point
        Absolute position on screen.
    size_hint : SizeHint
        Size as a proportion of parent's height and width.
    pos_hint : PosHint
        Position as a proportion of parent's height and width.
    background_char : str | None
        The background character of the widget if the widget is not transparent.
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
    update_theme:
        Paint the widget with current theme.
    update_off:
        Paint the "off" state.
    update_on:
        Paint the "on" state.
    on_toggle:
        Called when the toggle state changes.
    update_normal:
        Paint the normal state.
    update_hover:
        Paint the hover state.
    update_down:
        Paint the down state.
    on_release:
        Triggered when a button is released.
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point collides with an uncovered portion of widget.
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

    def __init__(
        self,
        *,
        background_char=" ",
        label: str = "",
        callback: Callable[[ToggleState], None] = lambda state: None,
        group: None | Hashable = None,
        allow_no_selection: bool = False,
        toggle_state: ToggleState = ToggleState.OFF,
        always_release: bool = False,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_color_pair: ColorPair | None = None,
    ):
        self.normal_color_pair = (0,) * 6  # Temporary assignment

        self._label_widget = TextWidget(
            pos_hint={"y_hint": 0.0, "x_hint": 0.0, "anchor": "left"}
        )

        self.callback = callback  # This must be set before `super().__init__`.

        super().__init__(
            background_char=background_char,
            group=group,
            allow_no_selection=allow_no_selection,
            toggle_state=toggle_state,
            always_release=always_release,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
            background_color_pair=background_color_pair,
        )

        self.add_widget(self._label_widget)

        self.label = label

    def update_theme(self):
        match self.state:
            case ButtonState.NORMAL:
                self.update_normal()
            case ButtonState.HOVER:
                self.update_hover()
            case ButtonState.DOWN:
                self.update_down()

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, label: str):
        self._label = label

        if self.group is None:
            if self.toggle_state is ToggleState.OFF:
                prefix = CHECK_OFF
            else:
                prefix = CHECK_ON
        else:
            if self.toggle_state is ToggleState.OFF:
                prefix = TOGGLE_OFF
            else:
                prefix = TOGGLE_ON

        text = prefix + label
        self._label_widget.size = 1, wcswidth(text)
        self._label_widget.apply_hints()
        self._label_widget.add_str(text)

    def update_hover(self):
        self.background_color_pair = self._label_widget.colors[
            :
        ] = self.color_theme.button_hover

    def update_down(self):
        self.background_color_pair = self._label_widget.colors[
            :
        ] = self.color_theme.button_press

    def update_normal(self):
        self.background_color_pair = self._label_widget.colors[
            :
        ] = self.color_theme.button_normal

    def on_toggle(self):
        if (
            self._label_widget.parent is not None
        ):  # This will be false during initialization.
            self.label = self.label  # Update radio button/checkbox
        self.callback(self.toggle_state)
