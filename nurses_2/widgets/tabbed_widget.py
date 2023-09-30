"""
A tabbed widget.
"""
import asyncio
from math import ceil

from ..colors import ColorPair, lerp_colors
from .behaviors.themable import Themable
from .behaviors.toggle_button_behavior import (
    ButtonState,
    ToggleButtonBehavior,
    ToggleState,
)
from .text_widget import TextWidget
from .widget import Point, PosHint, PosHintDict, Size, SizeHint, SizeHintDict, Widget

__all__ = [
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
    "TabbedWidget",
]

# TODO: Movable tabs?
TAB_SPACING = 3


class _Tab(Themable, ToggleButtonBehavior, TextWidget):
    def __init__(self, title, content, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
        self.set_text(title)

    def on_toggle(self):
        if self.parent is None:
            return
        if self.toggle_state is ToggleState.ON:
            self.content.is_enabled = True

            tabbed = self.parent.parent

            tabbed._history.remove(self.title)
            tabbed._history.append(self.title)

            tabbed._tab_underline.width = self.width + 2
            tabbed._tab_underline.x = self.x - 1

            tabbed._active_tab = self.title

            if tabbed._underline_task is not None:
                tabbed._underline_task.cancel()
            tabbed._underline_task = asyncio.create_task(tabbed._animate_underline())
        else:
            self.content.is_enabled = False

    def _update(self):
        if self.toggle_state is ToggleState.ON:
            self.colors[:] = self.color_theme.titlebar_normal
            self.canvas["bold"] = True
        elif self.state is ButtonState.HOVER:
            self.colors[:] = self.hover_color_pair
            self.canvas["bold"] = False
        else:
            self.colors[:] = self.color_theme.titlebar_inactive
            self.canvas["bold"] = False

    update_hover = _update
    update_normal = _update
    update_on = _update
    update_off = _update

    def update_theme(self):
        self.hover_color_pair = lerp_colors(
            self.color_theme.titlebar_normal,
            self.color_theme.titlebar_inactive,
            0.5,
        )
        self._update()


class TabbedWidget(Themable, Widget):
    """
    A tabbed widget.

    Parameters
    ----------
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
    add_tab:
        Add a new tab.
    remove_tab:
        Remove a tab.
    update_theme:
        Paint the widget with current theme.
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

        self.tabs: dict[str, Widget] = {}

        h, w = self.size
        self.tab_bar = Widget(size_hint={"width_hint": 1.0}, size=(1, w))

        self.separator = TextWidget(
            size_hint={"width_hint": 1.0}, size=(1, w), pos=(1, 0)
        )

        def _update_sep():
            self.separator.canvas["char"] = "━"

        self.separator.subscribe(self, "size", _update_sep)

        self.tab_window = Widget(size=(h - 2, w), pos=(2, 0))

        def _update_tabs():
            self.tab_window.size = self.height - 2, self.width

        self.tab_window.subscribe(self, "size", _update_tabs)

        self._tab_underline = TextWidget(size=(1, 1), pos=(1, 0), is_enabled=False)

        self._active_tab = None
        self._history = []  # Used to select the last viewed tab when a tab is removed.
        self._underline_task = None

        self.add_widgets(
            self.tab_bar, self.separator, self._tab_underline, self.tab_window
        )

    async def _animate_underline(self):
        underline = self._tab_underline

        underline.is_enabled = True
        underline.colors[:] = self.color_theme.titlebar_inactive
        underline.canvas["bold"] = False

        i = ceil(underline.width / 2) - 2
        while i >= 0:
            underline.canvas["bold"][0, i:-i] = True
            underline.colors[0, i + 1 : -i - 1] = self.color_theme.titlebar_normal
            underline.canvas["char"] = "━"
            underline.canvas["char"][0, i] = "╸"
            underline.canvas["char"][0, -i - 1] = "╺"
            i -= 1
            await asyncio.sleep(0.03)

    def _reposition_tabs(self):
        x = 1
        for child in self.tab_bar.children:
            child.x = x
            x += child.width + TAB_SPACING

    def update_theme(self):
        title_inactive = self.color_theme.titlebar_inactive
        self.tab_bar.background_color_pair = title_inactive
        self.tab_window.background_color_pair = title_inactive
        self.separator.default_color_pair = title_inactive
        self.separator.colors[:] = title_inactive

        title_active = self.color_theme.titlebar_normal
        self._tab_underline.default_color_pair = title_active
        self._tab_underline.colors[:] = title_active

    def add_tab(self, title: str, content: Widget):
        """
        Add a new tab. Tab titles are unique.

        Parameters
        ----------
        title : str
            Title of tab.
        content : Widget
            Content of the tab.
        """
        if title in self.tabs:
            raise ValueError("Tab already exists.")

        tab = _Tab(title, content, group=id(self))
        self.tabs[title] = tab

        self.tab_bar.add_widget(tab)
        self._reposition_tabs()

        self.tab_window.add_widget(content)
        self._history.append(title)
        self.tabs[title].toggle_state = ToggleState.ON

    def remove_tab(self, title: str):
        """
        Remove a tab.

        Parameters
        ----------
        title : str
            Title of the tab to remove.
        """
        if title not in self.tabs:
            raise ValueError("Tab doesn't exist.")

        tab = self.tabs.pop(title)
        self.tab_window.remove_widget(tab.content)
        self.tab_bar.remove_widget(tab)
        self._history.remove(title)
        self._reposition_tabs()

        if self._active_tab is title:
            if self._history:
                self._active_tab = self._history[-1]
                self.tabs[self._active_tab].toggle_state = ToggleState.ON
            else:
                self._active_tab = None
                self._tab_underline.is_enabled = False
        else:
            self._tab_underline.x = self.tabs[self._active_tab].x - 1
