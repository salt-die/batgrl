import asyncio

from collections.abc import Callable, Hashable

from ..colors import Color, GREEN, BLACK
from ..data_structures import Point
from .behaviors.toggle_button_behavior import ToggleButtonBehavior, ToggleState
from .text_widget import TextWidget, add_text
from .widget import Widget

HORIZONTAL_BLOCKS = "▊▋▌▍▎▏"
DARK_GREY = Color.from_hex("333333")
LIGHT_GREY = Color.from_hex("666666")


class _AnimatedToggle(ToggleButtonBehavior, TextWidget):
    def __init__(self, group, allow_no_selection, toggle_state, always_release, bg_color):
        super().__init__(
            size=(3, 4),
            pos_hint=(.5, .5),
            anchor="center",
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
            self.canvas["char"][1, 1:3] = HORIZONTAL_BLOCKS[i]
            await asyncio.sleep(.05)

        self.parent.callback(self.toggle_state)

    def on_toggle(self):
        if not hasattr(self, "_animation_task"):
            # Initializing...
            return
        self._animation_task.cancel()
        self._animation_task = asyncio.create_task(self._animate_toggle())


class FlatToggle(Widget):
    """
    An animated toggle button widget.

    Parameters
    ----------
    callback : Callable[[ToggleState], None], default: lambda state: None
        Called when toggle state changes. The new state is provided as first argument.
    toggle_background_color: Color, default: BLACK
        Background color of toggle.
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to True allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button. If button is in a group and :attr:`allow_no_selection`
        is `False` this value will be ignored if all buttons would be "off".
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
        size : Size, default: Size(10, 10)
        Size of widget.
    size : Size, default: Size(3, 4)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over :attr:`size`.
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over :attr:`pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        The point of the widget attached to :attr:`pos_hint`.
    is_transparent : bool, default: False
        If true, background_char and background_color_pair won't be painted.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    background_char : str | None, default: None
        The background character of the widget if not `None` and if the widget
        is not transparent.
    background_color_pair : ColorPair | None, default: None
        The background color pair of the widget if not `None` and if the
        widget is not transparent.

    Attributes
    ----------
    callback : Callable[[ToggleState], None]
        Toggle button callback.
    toggle_background: Color, default: BLACK
        Background color of toggle.
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
        Position relative to parent.
    top : int
        Y-coordinate of position.
    y : int
        Y-coordinate of position.
    left : int
        X-coordinate of position.
    x : int
        X-coordinate of position.
    bottom : int
        :attr:`top` + :attr:`height`.
    right : int
        :attr:`left` + :attr:`width`.
    absolute_pos : Point
        Absolute position on screen.
    center : Point
        Center of widget in local coordinates.
    size_hint : SizeHint
        Size as a proportion of parent's size.
    height_hint : float | None
        Height as a proportion of parent's height.
    width_hint : float | None
        Width as a proportion of parent's width.
    min_height : int
        Minimum height allowed when using :attr:`size_hint`.
    max_height : int
        Maximum height allowed when using :attr:`size_hint`.
    min_width : int
        Minimum width allowed when using :attr:`size_hint`.
    max_width : int
        Maximum width allowed when using :attr:`size_hint`.
    pos_hint : PosHint
        Position as a proportion of parent's size.
    y_hint : float | None
        Vertical position as a proportion of parent's size.
    x_hint : float | None
        Horizontal position as a proportion of parent's size.
    anchor : Anchor
        Determines which point is attached to :attr:`pos_hint`.
    background_char : str | None
        Background character.
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
    on_size:
        Called when widget is resized.
    apply_hints:
        Apply size and pos hints.
    to_local:
        Convert point in absolute coordinates to local coordinates.
    collides_point:
        True if point is within widget's bounding box.
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
        Yield all descendents (or ancestors if `reverse` is True).
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
        size: Point=Point(3, 4),
        callback: Callable[[ToggleState], None]=lambda state: None,
        toggle_background_color: Color=BLACK,
        group: None | Hashable=None,
        allow_no_selection: bool=False,
        toggle_state: ToggleState=ToggleState.OFF,
        always_release: bool=False,
        **kwargs
    ):
        super().__init__(size=size, **kwargs)

        self.callback = callback

        self._toggle = _AnimatedToggle(
            group=group,
            allow_no_selection=allow_no_selection,
            toggle_state=toggle_state,
            always_release=always_release,
            bg_color=toggle_background_color,
        )
        self.add_widget(self._toggle)

    @property
    def toggle_background_color(self) -> Color:
        return Color(*self._toggle[0, 0, 3:])

    @toggle_background_color.setter
    def toggle_background_color(self, color: Color):
        self._toggle.colors[[0, -1], :, 3:] = color
