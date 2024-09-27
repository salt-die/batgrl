"""A tabbed gadget."""

import asyncio

from ..colors import lerp_colors
from .behaviors.themable import Themable
from .behaviors.toggle_button_behavior import ToggleButtonBehavior
from .gadget import Gadget, Point, PosHint, Size, SizeHint, new_cell
from .pane import Pane
from .text import Text

__all__ = ["Tabs", "Point", "Size"]

# TODO: Movable tabs?
TAB_SPACING = 3


class _Tab(Themable, ToggleButtonBehavior, Text):
    def __init__(self, title, content, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.content = content
        self.set_text(title)

    def on_toggle(self):
        if self.parent is None:
            return
        if self.toggle_state == "on":
            self.content.is_enabled = True

            tabbed: Tabs = self.parent.parent

            tabbed._history.remove(self.title)
            tabbed._history.append(self.title)

            tabbed._active_tab = self.title

            if tabbed._underline_task is not None:
                tabbed._underline_task.cancel()
            tabbed._underline_task = asyncio.create_task(
                tabbed._tab_underline.tween(
                    duration=0.5,
                    easing="out_bounce",
                    x=self.x - 1,
                    width=self.width + 2,
                )
            )
        else:
            self.content.is_enabled = False

    def _update(self):
        if self.toggle_state == "on":
            color_pair = self.color_theme.titlebar_normal
            bold = True
        elif self.button_state == "hover":
            color_pair = self.hover_color_pair
            bold = False
        else:
            color_pair = self.color_theme.titlebar_inactive
            bold = False
        self.canvas[["fg_color", "bg_color"]] = color_pair
        self.canvas["bold"] = bold

    update_hover = _update
    update_normal = _update
    update_on = _update
    update_off = _update

    def update_theme(self):
        normal = self.color_theme.titlebar_normal
        inactive = self.color_theme.titlebar_inactive
        self.hover_color_pair = (
            lerp_colors(normal.fg, inactive.fg, 0.5),
            lerp_colors(normal.bg, inactive.bg, 0.5),
        )
        self._update()


class Tabs(Themable, Gadget):
    r"""
    A tabbed gadget.

    Parameters
    ----------
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
    add_tab(title, content)
        Add a new tab.
    remove_tab(title)
        Remove a tab.
    update_theme()
        Paint the gadget with current theme.
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
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
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

        self.tabs: dict[str, Gadget] = {}

        h, w = self.size
        self.tab_bar = Pane(size_hint={"width_hint": 1.0}, size=(1, w))
        self.separator = Text(size_hint={"width_hint": 1.0}, size=(1, w), pos=(1, 0))

        def _update_sep():
            self.separator.canvas["char"] = "━"

        self.bind("size", _update_sep)

        self.tab_window = Pane(
            size=(h - 2, w),
            pos=(2, 0),
            size_hint={"height_hint": 1.0, "width_hint": 1.0, "height_offset": -2},
        )

        title_fg, title_bg = self.color_theme.titlebar_normal
        tab_style = {"bold": True, "fg_color": title_fg, "bg_color": title_bg}
        self._tab_underline = Text(
            size=(1, 1),
            pos=(1, 0),
            is_enabled=False,
            default_cell=new_cell(char="━", **tab_style),
        )
        tab_underline_left = Text(
            size=(1, 1),
            default_cell=new_cell(char="╺", **tab_style),
        )
        tab_underline_right = Text(
            size=(1, 1),
            pos_hint={"x_hint": 1.0, "anchor": "right"},
            default_cell=new_cell(char="╸", **tab_style),
        )
        self._tab_underline.add_gadgets(tab_underline_left, tab_underline_right)

        self._active_tab = None
        self._history = []  # Used to select the last viewed tab when a tab is removed.
        self._underline_task = None

        self.add_gadgets(
            self.tab_bar, self.separator, self._tab_underline, self.tab_window
        )

    def _reposition_tabs(self):
        x = 1
        for child in self.tab_bar.children:
            child.x = x
            x += child.width + TAB_SPACING

    def update_theme(self):
        """Paint the gadget with current theme."""
        title_inactive = self.color_theme.titlebar_inactive
        self.tab_bar.bg_color = title_inactive.bg
        self.tab_window.bg_color = title_inactive.bg
        self.separator.default_cell[["fg_color", "bg_color"]] = title_inactive
        self.separator.canvas[["fg_color", "bg_color"]] = title_inactive

        title_active = self.color_theme.titlebar_normal
        self._tab_underline.default_cell[["fg_color", "bg_color"]] = title_active
        self._tab_underline.canvas[["fg_color", "bg_color"]] = title_active

    def add_tab(self, title: str, content: Gadget):
        """
        Add a new tab. Tab titles are unique.

        Parameters
        ----------
        title : str
            Title of tab.
        content : Gadget
            Content of the tab.
        """
        if title in self.tabs:
            raise ValueError("Tab already exists.")

        tab = _Tab(title, content, group=id(self))
        self.tabs[title] = tab

        self.tab_bar.add_gadget(tab)
        self._reposition_tabs()

        self.tab_window.add_gadget(content)
        self._history.append(title)
        self.tabs[title].toggle_state = "on"
        self._tab_underline.is_enabled = True

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
        self.tab_window.remove_gadget(tab.content)
        self.tab_bar.remove_gadget(tab)
        self._history.remove(title)
        self._reposition_tabs()

        if self._active_tab is title:
            if self._history:
                self._active_tab = self._history[-1]
                self.tabs[self._active_tab].toggle_state = "on"
            else:
                self._active_tab = None
                self._tab_underline.is_enabled = False
        else:
            self._tab_underline.x = self.tabs[self._active_tab].x - 1
