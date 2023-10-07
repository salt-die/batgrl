"""
A scrollable view gadget.
"""
from ..colors import DEFAULT_COLOR_THEME, Color, ColorPair
from ..io import KeyEvent, MouseButton, MouseEvent, MouseEventType
from .behaviors.grabbable import Grabbable
from .gadget import (
    Gadget,
    Point,
    PosHint,
    PosHintDict,
    Size,
    SizeHint,
    SizeHintDict,
    clamp,
    subscribable,
)
from .text import Text
from .text_tools import smooth_horizontal_bar, smooth_vertical_bar

__all__ = [
    "DEFAULT_INDICATOR_HOVER",
    "DEFAULT_INDICATOR_NORMAL",
    "DEFAULT_INDICATOR_PRESS",
    "DEFAULT_SCROLLBAR_COLOR",
    "Point",
    "PosHint",
    "PosHintDict",
    "ScrollView",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

DEFAULT_SCROLLBAR_COLOR = Color.from_hex("070C25")
DEFAULT_INDICATOR_NORMAL = Color.from_hex("0E1843")
DEFAULT_INDICATOR_HOVER = Color.from_hex("111E4F")
DEFAULT_INDICATOR_PRESS = Color.from_hex("172868")


class _ScrollBarBase(Grabbable, Text):
    length: int

    def __init__(self):
        super().__init__(size=(1, 2))
        self.indicator_proportion: float = 1.0
        self.indicator_progress: float = 0.0
        self.is_hovered = False

    @property
    def indicator_proportion(self) -> float:
        return self._indicator_proportion

    @indicator_proportion.setter
    def indicator_proportion(self, indicator_porportion: float):
        self._indicator_proportion = indicator_porportion
        self._set_indicator_length()

    @property
    def fill_length(self) -> float:
        """The length the indicator can travel."""
        return self.length - self.indicator_length

    def paint_indicator(self) -> tuple[Color, int, float]:
        sv: ScrollView = self.parent

        if self.is_grabbed:
            indicator_color = sv._indicator_press_color
        elif self.is_hovered:
            indicator_color = sv._indicator_hover_color
        else:
            indicator_color = sv._indicator_normal_color

        self.canvas["char"] = " "

        self.colors[..., :3] = indicator_color
        self.colors[..., 3:] = sv._scrollbar_color

        start, offset = divmod(self.indicator_progress * self.fill_length, 1)
        start = int(start)
        # Round offset to the nearest 1/8th.
        offset = round(offset * 8) / 8
        if offset == 1:
            offset -= 1
            start += 1

        return indicator_color, start, offset

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self.paint_indicator()


class _VerticalScrollbar(_ScrollBarBase):
    @property
    def length(self) -> int:
        return self.height

    def _set_indicator_length(self):
        self.indicator_length = clamp(
            2, round(self.indicator_proportion * self.length), self.length
        )

    def paint_indicator(self):
        indicator_color, start, offset = super().paint_indicator()

        sv: ScrollView = self.parent
        smooth_bar = smooth_vertical_bar(
            self.indicator_length, 1, offset, reversed=True
        )
        stop = start + len(smooth_bar)
        self.canvas["char"][start:stop].T[:] = smooth_bar

        y_offset = offset != 0
        self.colors[start + y_offset : stop, :, :3] = sv._scrollbar_color
        self.colors[start + y_offset : stop, :, 3:] = indicator_color

    def on_mouse(self, mouse_event):
        old_hovered = self.is_hovered

        y, x = self.to_local(mouse_event.position)
        start = round(self.indicator_progress * self.fill_length)
        self.is_hovered = 0 <= x < 2 and start <= y < start + self.indicator_length

        if super().on_mouse(mouse_event):
            return True

        if old_hovered != self.is_hovered:
            self.paint_indicator()

    def grab(self, mouse_event):
        super().grab(mouse_event)

        if self.is_hovered:
            self.paint_indicator()
        else:
            self.is_hovered = True

            sv: ScrollView = self.parent
            if self.fill_length == 0:
                sv.vertical_proportion = 0
            else:
                sv.vertical_proportion = (
                    self.to_local(mouse_event.position).y / self.length
                )

    def grab_update(self, mouse_event):
        sv: ScrollView = self.parent
        if self.fill_length == 0:
            sv.vertical_proportion = 0
        else:
            sv.vertical_proportion += self.mouse_dy / self.fill_length


class _HorizontalScrollbar(_ScrollBarBase):
    @property
    def length(self):
        return self.width

    def _set_indicator_length(self):
        self.indicator_length = clamp(
            4, round(self.indicator_proportion * self.length), self.length
        )

    def paint_indicator(self):
        indicator_color, start, offset = super().paint_indicator()

        sv: ScrollView = self.parent
        smooth_bar = smooth_horizontal_bar(self.indicator_length, 1, offset)
        self.canvas["char"][:, start : start + len(smooth_bar)] = smooth_bar
        if offset != 0:
            self.colors[:, start, :3] = sv._scrollbar_color
            self.colors[:, start, 3:] = indicator_color

    def on_mouse(self, mouse_event):
        old_hovered = self.is_hovered

        y, x = self.to_local(mouse_event.position)
        start = round(self.indicator_progress * self.fill_length)
        self.is_hovered = y == 0 and start <= x < start + self.indicator_length

        if super().on_mouse(mouse_event):
            return True

        if old_hovered != self.is_hovered:
            self.paint_indicator()

    def grab(self, mouse_event):
        super().grab(mouse_event)
        if self.is_hovered:
            self.paint_indicator()
        else:
            self.is_hovered = True

            sv: ScrollView = self.parent
            if self.fill_length == 0:
                sv.horizontal_proportion = 0
            else:
                sv.horizontal_proportion = (
                    self.to_local(mouse_event.position).x / self.length
                )

    def grab_update(self, mouse_event):
        sv: ScrollView = self.parent
        if self.fill_length == 0:
            sv.horizontal_proportion = 0
        else:
            sv.horizontal_proportion += self.mouse_dx / self.fill_length


class ScrollView(Grabbable, Gadget):
    """
    A scrollable view gadget.

    The view can be set with the :attr:`view` property, e.g.,
    ``my_scrollview.view = some_gadget``.

    Parameters
    ----------
    allow_vertical_scroll : bool, default: True
        Allow vertical scrolling.
    allow_horizontal_scroll : bool, default: True
        Allow horizontal scrolling.
    show_vertical_bar : bool, default: True
        Show the vertical scrollbar.
    show_horizontal_bar : bool, default: True
        Show the horizontal scrollbar.
    scrollwheel_enabled : bool, default: True
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool, default: True
        Allow scrolling with arrow keys.
    scrollbar_color : Color, default: DEFAULT_SCROLLBAR_COLOR
        Background color of scrollbar.
    indicator_normal_color : Color, default: DEFAULT_INDICATOR_NORMAL
        Scrollbar indicator normal color.
    indicator_hover_color : Color, default: DEFAULT_INDICATOR_HOVER
        Scrollbar indicator hover color.
    indicator_press_color : Color, default: DEFAULT_INDICATOR_PRESS
        Scrollbar indicator press color.
    is_grabbable : bool, default: True
        If false, grabbable behavior is disabled.
    disable_ptf : bool, default: False
        If true, gadget will not be pulled to front when grabbed.
    mouse_button : MouseButton, default: MouseButton.LEFT
        Mouse button used for grabbing.
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
    background_color_pair : ColorPair | None, default: DEFAULT_COLOR_THEME.primary
        The background color pair of the gadget if the gadget is not transparent.

    Attributes
    ----------
    view : Gadget | None
        The scrolled gadget.
    allow_vertical_scroll : bool
        Allow vertical scrolling.
    allow_horizontal_scroll : bool
        Allow horizontal scrolling.
    show_vertical_bar : bool
        Show the vertical scrollbar.
    show_horizontal_bar : bool
        Show the horizontal scrollbar.
    scrollwheel_enabled : bool
        Allow vertical scrolling with scrollwheel.
    arrow_keys_enabled : bool
        Allow scrolling with arrow keys.
    scrollbar_color : Color
        Background color of scrollbar.
    indicator_normal_color : Color
        Scrollbar indicator normal color.
    indicator_hover_color : Color
        Scrollbar indicator hover color.
    indicator_press_color : Color
        Scrollbar indicator press color.
    vertical_proportion : float
        Vertical scroll position as a proportion of total.
    horizontal_proportion : float
        Horizontal scroll position as a proportion of total.
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
    grab:
        Grab the gadget.
    ungrab:
        Ungrab the gadget.
    grab_update:
        Update gadget with incoming mouse events while grabbed.
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
        allow_vertical_scroll: bool = True,
        allow_horizontal_scroll: bool = True,
        show_vertical_bar: bool = True,
        show_horizontal_bar: bool = True,
        scrollwheel_enabled: bool = True,
        arrow_keys_enabled: bool = True,
        scrollbar_color: Color = DEFAULT_SCROLLBAR_COLOR,
        indicator_normal_color: Color = DEFAULT_INDICATOR_NORMAL,
        indicator_hover_color: Color = DEFAULT_INDICATOR_HOVER,
        indicator_press_color: Color = DEFAULT_INDICATOR_PRESS,
        is_grabbable: bool = True,
        disable_ptf: bool = False,
        mouse_button: MouseButton = MouseButton.LEFT,
        size=Size(10, 10),
        pos=Point(0, 0),
        size_hint: SizeHint | SizeHintDict | None = None,
        pos_hint: PosHint | PosHintDict | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
        background_char: str | None = None,
        background_color_pair: ColorPair | None = DEFAULT_COLOR_THEME.primary,
    ):
        super().__init__(
            is_grabbable=is_grabbable,
            disable_ptf=disable_ptf,
            mouse_button=mouse_button,
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
        self.allow_vertical_scroll = allow_vertical_scroll
        self.allow_horizontal_scroll = allow_horizontal_scroll
        self.scrollwheel_enabled = scrollwheel_enabled
        self.arrow_keys_enabled = arrow_keys_enabled

        self._scrollbar_color = scrollbar_color
        self._indicator_normal_color = indicator_normal_color
        self._indicator_hover_color = indicator_hover_color
        self._indicator_press_color = indicator_press_color

        self._vertical_proportion = 0
        self._horizontal_proportion = 0
        self._corner = Gadget(
            size=(1, 2),
            pos_hint={"y_hint": 1.0, "x_hint": 1.0, "anchor": "bottom-right"},
            background_color_pair=scrollbar_color * 2,
            is_enabled=show_horizontal_bar and show_vertical_bar,
        )
        self._vertical_bar = _VerticalScrollbar()
        self._horizontal_bar = _HorizontalScrollbar()
        self._view = None

        self.add_gadgets(self._corner, self._vertical_bar, self._horizontal_bar)

        self.show_horizontal_bar = show_horizontal_bar
        self.show_vertical_bar = show_vertical_bar

    @property
    def show_vertical_bar(self) -> bool:
        return self._vertical_bar.is_enabled

    @show_vertical_bar.setter
    @subscribable
    def show_vertical_bar(self, show: bool):
        self._vertical_bar.is_enabled = show
        self.on_size()

    @property
    def show_horizontal_bar(self) -> bool:
        return self._horizontal_bar.is_enabled

    @show_horizontal_bar.setter
    @subscribable
    def show_horizontal_bar(self, show: bool):
        self._horizontal_bar.is_enabled = show
        self.on_size()

    @property
    def scrollbar_color(self) -> Color:
        return self._scrollbar_color

    @scrollbar_color.setter
    def scrollbar_color(self, scrollbar_color: Color):
        self._scrollbar_color = scrollbar_color
        self._corner.background_color_pair = scrollbar_color * 2
        self._update_port_and_scrollbar()

    @property
    def indicator_normal_color(self) -> Color:
        return self._indicator_normal_color

    @indicator_normal_color.setter
    def indicator_normal_color(self, indicator_normal_color: Color):
        self._indicator_normal_color = indicator_normal_color
        self._update_port_and_scrollbar()

    @property
    def indicator_hover_color(self) -> Color:
        return self._indicator_hover_color

    @indicator_hover_color.setter
    def indicator_hover_color(self, indicator_hover_color: Color):
        self._indicator_hover_color = indicator_hover_color
        self._update_port_and_scrollbar()

    @property
    def indicator_press_color(self) -> Color:
        return self._indicator_press_color

    @indicator_press_color.setter
    def indicator_press_color(self, indicator_press_color: Color):
        self._indicator_press_color = indicator_press_color
        self._update_port_and_scrollbar()

    @property
    def vertical_proportion(self) -> float:
        return self._vertical_proportion

    @vertical_proportion.setter
    @subscribable
    def vertical_proportion(self, vertical_proportion: float):
        if self.allow_vertical_scroll:
            if self._view is None or self.total_vertical_distance <= 0:
                self._vertical_proportion = 0
            else:
                self._vertical_proportion = clamp(vertical_proportion, 0, 1)
            self._update_port_and_scrollbar()

    @property
    def horizontal_proportion(self) -> float:
        return self._horizontal_proportion

    @horizontal_proportion.setter
    @subscribable
    def horizontal_proportion(self, horizontal_proportion: float):
        if self.allow_horizontal_scroll:
            if self._view is None or self.total_horizontal_distance <= 0:
                self._horizontal_proportion = 0
            else:
                self._horizontal_proportion = clamp(horizontal_proportion, 0, 1)
            self._update_port_and_scrollbar()

    @property
    def port_height(self) -> int:
        return self.height - self.show_horizontal_bar

    @property
    def port_width(self) -> int:
        return self.width - self.show_vertical_bar * 2

    @property
    def total_vertical_distance(self) -> int:
        """The distance the view can scroll vertically."""
        return 0 if self._view is None else max(0, self._view.height - self.port_height)

    @property
    def total_horizontal_distance(self) -> int:
        """The distance the view can scroll horizontally."""
        return 0 if self._view is None else max(0, self._view.width - self.port_width)

    def _update_port_and_scrollbar(self):
        """Move port and repaint scrollbar."""
        if self._view is None:
            self._vertical_bar.indicator_proportion = 1.0
            self._vertical_bar.indicator_progress = 0
            self._vertical_bar.paint_indicator()
            self._horizontal_bar.indicator_proportion = 1.0
            self._horizontal_bar.indicator_progress = 0
            self._horizontal_bar.paint_indicator()
        else:
            self._view.top = -round(
                self.vertical_proportion * self.total_vertical_distance
            )
            self._view.left = -round(
                self.horizontal_proportion * self.total_horizontal_distance
            )

            self._vertical_bar.indicator_proportion = clamp(
                self.port_height / self._view.height, 0, 1
            )
            self._vertical_bar.indicator_progress = self.vertical_proportion
            self._vertical_bar.paint_indicator()

            self._horizontal_bar.indicator_proportion = clamp(
                self.port_width / self._view.width, 0, 1
            )
            self._horizontal_bar.indicator_progress = self.horizontal_proportion
            self._horizontal_bar.paint_indicator()

    @property
    def view(self) -> Gadget | None:
        return self._view

    @view.setter
    def view(self, view: Gadget | None):
        if self._view is not None:
            self.remove_gadget(self._view)

        self._view = view

        if view is not None:
            self.add_gadget(view)
            self.children.insert(0, self.children.pop())  # Move view below scrollbars.

            def update_proportion():
                y, x = self._view.pos
                h = self.total_vertical_distance
                w = self.total_horizontal_distance
                self.vertical_proportion = 0 if h == 0 else -y / h
                self.horizontal_proportion = 0 if w == 0 else -x / w

            self.subscribe(view, "size", update_proportion)
            self._update_port_and_scrollbar()

    def remove_gadget(self, gadget: Gadget):
        if gadget is self._view:
            self._view = None
            self.unsubscribe(gadget, "size")

        super().remove_gadget(gadget)

    def on_size(self):
        self._vertical_bar.height = self.height - self.show_horizontal_bar
        self._vertical_bar.left = self.width - 2
        self._horizontal_bar.width = self.width - 2 * self.show_vertical_bar
        self._horizontal_bar.top = self.height - 1
        self._update_port_and_scrollbar()

    def on_key(self, key_event: KeyEvent) -> bool | None:
        if not self.arrow_keys_enabled:
            return False

        match key_event.key:
            case "up":
                self._scroll_up()
            case "down":
                self._scroll_down()
            case "left":
                self._scroll_left()
            case "right":
                self._scroll_right()
            case _:
                return super().on_key(key_event)

        return True

    def grab_update(self, mouse_event: MouseEvent):
        self._scroll_up(self.mouse_dy)
        self._scroll_left(self.mouse_dx)

    def _scroll_left(self, n=1):
        if self._view is not None:
            if self.total_horizontal_distance == 0:
                self.horizontal_proportion = 0
            else:
                self.horizontal_proportion = clamp(
                    (-self.view.left - n) / self.total_horizontal_distance, 0, 1
                )

    def _scroll_right(self, n=1):
        self._scroll_left(-n)

    def _scroll_up(self, n=1):
        if self._view is not None:
            if self.total_vertical_distance == 0:
                self.vertical_proportion = 0
            else:
                self.vertical_proportion = clamp(
                    (-self.view.top - n) / self.total_vertical_distance, 0, 1
                )

    def _scroll_down(self, n=1):
        self._scroll_up(-n)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        if self.scrollwheel_enabled and self.collides_point(mouse_event.position):
            match mouse_event.event_type:
                case MouseEventType.SCROLL_UP:
                    self._scroll_up()
                    return True
                case MouseEventType.SCROLL_DOWN:
                    self._scroll_down()
                    return True

        return super().on_mouse(mouse_event)
