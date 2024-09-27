"""A menu and menu bar gadget."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from inspect import signature
from typing import Self

from batgrl.terminal.events import KeyEvent

from ..geometry import clamp
from .behaviors.themable import Themable
from .behaviors.toggle_button_behavior import ToggleButtonBehavior, ToggleState
from .grid_layout import GridLayout
from .pane import Pane, Point, PosHint, Size, SizeHint
from .text import Text, str_width

__all__ = ["Menu", "MenuBar", "MenuDict", "Point", "Size"]

type ItemCallback = Callable[[], None] | Callable[[ToggleState], None]
type MenuDict = dict[tuple[str, str], ItemCallback | MenuDict]
NESTED_SUFFIX = " ▶"
CHECK_OFF = "□"
CHECK_ON = "▣"


def nargs(callable: Callable) -> int:
    """Return the number of arguments of `callable`."""
    return len(signature(callable).parameters)


class _MenuItem(Themable, ToggleButtonBehavior, Pane):
    def __init__(
        self,
        *,
        left_label: str = "",
        right_label: str = "",
        item_callback: ItemCallback = lambda: None,
        submenu: Menu | None = None,
        **kwargs,
    ):
        self.parent: Menu | None
        self.left_label = Text(size=(1, str_width(left_label)), alpha=0.0)
        self.right_label = Text(
            size=(1, str_width(right_label)),
            pos_hint={"x_hint": 1.0, "anchor": "right"},
            alpha=0.0,
        )
        self.item_callback = item_callback
        self.submenu = submenu
        super().__init__(**kwargs)

        self.left_label.add_str(left_label)
        self.right_label.add_str(right_label)
        self.add_gadgets(self.left_label, self.right_label)
        self.on_transparency()
        self.update_off()

    def _repaint(self):
        if self.button_state == "disallowed":
            color_pair = self.color_theme.menu_item_disallowed
        elif self.button_state == "normal":
            color_pair = self.color_theme.primary
        elif self.button_state == "hover" or self.button_state == "down":
            color_pair = self.color_theme.menu_item_hover
        self.bg_color = color_pair.bg
        self.left_label.canvas[["fg_color", "bg_color"]] = color_pair
        self.right_label.canvas[["fg_color", "bg_color"]] = color_pair

    @property
    def alpha(self) -> float:
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = alpha
        if self.submenu is not None:
            self.submenu.alpha = alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        self.left_label.is_transparent = self.is_transparent
        self.right_label.is_transparent = self.is_transparent
        if self.submenu is not None:
            self.submenu.is_transparent = self.is_transparent

    def update_theme(self):
        """Paint the gadget with current theme."""
        self._repaint()

    def update_hover(self):
        """Update parent menu and submenu on hover state."""
        self._repaint()

        index = self.parent.children.index(self)
        selected = self.parent._current_selection
        if not (selected == -1 or selected == index):
            self.parent.close_submenus()
            if selected != -1:
                last_hovered = self.parent.children[selected]
                last_hovered.button_state = "normal"

        self.parent._current_selection = index
        if self.submenu is not None:
            self.submenu.open_menu()

    def update_normal(self):
        """Update parent menu and submenu on normal state."""
        self._repaint()
        if self.parent is None:
            return

        if self.submenu is None or not self.submenu.is_enabled:
            if self.parent._current_selection == self.parent.children.index(self):
                self.parent._current_selection = -1
        elif not self.submenu.collides_point(self._last_mouse_pos):
            self.submenu.close_menu()

    def update_disallowed(self):
        self._repaint()
        if self.submenu is not None:
            self.submenu.close_menu()

    def update_off(self):
        """Paint the off state."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas["char"][0, 1] = CHECK_OFF

    def update_on(self):
        """Paint the on state."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas["char"][0, 1] = CHECK_ON

    def on_mouse(self, mouse_event):
        """Save last mouse position."""
        self._last_mouse_pos = mouse_event.pos
        return super().on_mouse(mouse_event)

    def on_release(self):
        """Open submenu or call item callback on release."""
        if self.submenu is not None:
            self.submenu.open_menu()
        elif nargs(self.item_callback) == 0:
            self.item_callback()

            if self.parent.close_on_release:
                self.parent.close_parents()
        else:
            super().on_release()

    def on_toggle(self):
        """Call item callback on toggle state change."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.item_callback(self.toggle_state)


class Menu(GridLayout):
    r"""
    A menu gadget.

    Menus are constructed with the class method :meth:`from_dict_of_dicts`. Each key of
    the dict should be a tuple of two strings for left and right labels and each value
    should be either a callable with no arguments for a normal menu item, a callable
    with one argument for a toggle menu item (the argument will be the toggle state of
    the menu item), or a dict (for a submenu).

    Once opened, a menu can be navigated with the mouse or arrow keys.

    Parameters
    ----------
    close_on_release : bool, default: True
        Whether to close the menu when an item is selected.
    close_on_click : bool, default: True
        Whether to close the menu when a click doesn't collide with it.
    alpha : float, default: 1.0
        Transparency of gadget.
    grid_rows : int, default: 1
        Number of rows.
    grid_columns : int, default: 1
        Number of columns.
    orientation : Orientation, default: "tb-lr"
        The orientation of the grid.
    padding_left : int, default: 0
        Padding on left side of grid.
    padding_right : int, default: 0
        Padding on right side of grid.
    padding_top : int, default: 0
        Padding at the top of grid.
    padding_bottom : int, default: 0
        Padding at the bottom of grid.
    horizontal_spacing : int, default: 0
        Horizontal spacing between children.
    vertical_spacing : int, default: 0
        Vertical spacing between children.
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
    close_on_release : bool
        Whether to close the menu when an item is selected.
    close_on_click : bool
        Whether to close the menu when a click doesn't collide with it.
    alpha : float
        Transparency of gadget.
    min_grid_size : Size
        Minimum grid size needed to show all children.
    grid_rows : int
        Number of rows.
    grid_columns : int
        Number of columns.
    orientation : Orientation
        The orientation of the grid.
    padding_left : int
        Padding on left side of grid.
    padding_right : int
        Padding on right side of grid.
    padding_top : int
        Padding at the top of grid.
    padding_bottom : int
        Padding at the bottom of grid.
    horizontal_spacing : int
        Horizontal spacing between children.
    vertical_spacing : int
        Vertical spacing between children.
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
    open_menu()
        Open menu.
    close_menu()
        Close menu.
    from_dict_of_dicts(...)
        Constructor to create a menu from a dict of dicts. This should be
        default way of constructing menus.
    index_at(row, col)
        Return index of gadget in :attr:`children` at position `row, col` in the grid.
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
        close_on_release: bool = True,
        close_on_click: bool = True,
        alpha: float = 1.0,
        orientation="tb-lr",
        grid_rows: int = 1,
        grid_columns: int = 1,
        padding_left: int = 0,
        padding_right: int = 0,
        padding_top: int = 0,
        padding_bottom: int = 0,
        horizontal_spacing: int = 0,
        vertical_spacing: int = 0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        super().__init__(
            orientation=orientation,
            grid_rows=grid_rows,
            grid_columns=grid_columns,
            padding_left=padding_left,
            padding_right=padding_right,
            padding_top=padding_top,
            padding_bottom=padding_bottom,
            horizontal_spacing=horizontal_spacing,
            vertical_spacing=vertical_spacing,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

        self.close_on_release = close_on_release
        self.close_on_click = close_on_click
        self._alpha = alpha

        self._parent_menu = None
        self._current_selection = -1
        self._submenus = []
        self._menu_button = None

    @property
    def alpha(self) -> float:
        """Transparency of gadget."""
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(alpha, 0.0, 1.0)
        for item in self.children:
            item.alpha = self._alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        for item in self.children:
            item.is_transparent = self.is_transparent

    def open_menu(self):
        """Open the menu."""
        self.is_enabled = True

    def close_menu(self):
        """Close the menu."""
        if self._menu_button is not None and self._menu_button.toggle_state == "on":
            self._menu_button.toggle_state = "off"
        else:
            if self._menu_button is not None:
                self._menu_button.update_off()

            self.is_enabled = False
            self._current_selection = -1
            self.close_submenus()

            for child in self.children:
                child.button_state = "normal"

    def close_submenus(self):
        """Close all submenus."""
        for menu in self._submenus:
            menu.close_menu()

    def close_parents(self):
        """Close all parent menus."""
        if self._parent_menu is not None:
            self._parent_menu.close_parents()
        else:
            self.close_menu()

    def on_mouse(self, mouse_event):
        """Close menus on non-colliding mouse down."""
        if (
            mouse_event.event_type == "mouse_down"
            and self.close_on_click
            and not (
                self.collides_point(mouse_event.pos)
                or any(
                    submenu.collides_point(mouse_event.pos)
                    for submenu in self._submenus
                )
            )
        ):
            self.close_menu()
            return False

        return super().on_mouse(mouse_event)

    def on_key(self, key_event):
        """Navigate menus with arrow keys and select menu items with enter."""
        for submenu in self._submenus:
            if submenu.is_enabled:
                if submenu.on_key(key_event):
                    return True
                else:
                    break

        if key_event.key == "up":
            i = self._current_selection
            if i == -1:
                i = len(self.children) - 1
            else:
                i = self._current_selection
                self.children[i].button_state = "normal"
                i = (i - 1) % len(self.children)

            for _ in self.children:
                if self.children[i].item_disabled:
                    i = (i - 1) % len(self.children)
                else:
                    self._current_selection = i
                    self.children[i]._hover()
                    self.close_submenus()
                    return True

            return False

        if key_event.key == "down":
            i = self._current_selection
            if i == -1:
                i = 0
            else:
                self.children[i].button_state = "normal"
                i = (i + 1) % len(self.children)

            for _ in self.children:
                if self.children[i].item_disabled:
                    i = (i + 1) % len(self.children)
                else:
                    self._current_selection = i
                    self.children[i]._hover()
                    self.close_submenus()
                    return True

            return False

        if key_event.key == "left":
            if self._current_selection != -1 and (
                (submenu := self.children[self._current_selection].submenu)
                and submenu.is_enabled
            ):
                submenu.close_menu()
                return True

        if key_event.key == "right":
            if self._current_selection != -1 and (
                (submenu := self.children[self._current_selection].submenu)
                and not submenu.is_enabled
            ):
                submenu.open_menu()
                if submenu.children:
                    submenu.children[0]._hover()
                    submenu.close_submenus()
                return True

        if key_event.key == "enter":
            if (
                self._current_selection != -1
                and (child := self.children[self._current_selection]).submenu is None
            ):
                if (n := nargs(child.item_callback)) == 0:
                    child.on_release()
                elif n == 1:
                    child._down()
                return True

        return super().on_key(key_event)

    @classmethod
    def from_dict_of_dicts(
        cls,
        menu: MenuDict,
        pos: Point = Point(0, 0),
        close_on_release: bool = True,
        close_on_click: bool = True,
        alpha: float = 1.0,
    ) -> Iterator[Self]:
        """
        Create and yield menus from a dict of dicts. Callables should either have no
        arguments for a normal menu item, or one argument for a toggle menu item.

        Parameters
        ----------
        menu : MenuDict
            The menu as a dict of dicts.
        pos : Point, default: Point(0, 0)
            Position of menu.
        close_on_release : bool, default: True
            Whether to close the menu when an item is selected.
        close_on_click : bool, default: True
            Whether to close the menu when a click doesn't collide with it.
        alpha : float, default: 1.0
            Transparency of gadget.

        Yields
        ------
        Menu
            The menu or one of its submenus.
        """
        height = len(menu)
        width = max(
            (
                str_width(right_label)
                + str_width(left_label)
                + 7
                + isinstance(callable_or_dict, dict) * 2
            )
            for (right_label, left_label), callable_or_dict in menu.items()
        )
        menu_gadget = cls(
            alpha=alpha,
            grid_rows=height,
            grid_columns=1,
            size=(height, width),
            pos=pos,
            close_on_release=close_on_release,
            close_on_click=close_on_click,
        )

        y, x = pos
        for i, ((left_label, right_label), value) in enumerate(menu.items()):
            if isinstance(value, Callable):
                menu_item = _MenuItem(
                    left_label=f"   {left_label}",
                    right_label=f"{right_label} ",
                    item_callback=value,
                    alpha=alpha,
                    size=(1, width),
                )
            elif isinstance(value, dict):
                submenus = Menu.from_dict_of_dicts(
                    value,
                    pos=(y + i, x + width),
                    close_on_release=close_on_release,
                    close_on_click=close_on_click,
                    alpha=alpha,
                )
                for submenu in submenus:
                    menu_gadget._submenus.append(submenu)
                    submenu._parent_menu = menu_gadget
                    submenu.is_enabled = False
                    yield submenu

                menu_item = _MenuItem(
                    left_label=f"   {left_label}",
                    right_label=f"{right_label}{NESTED_SUFFIX} ",
                    submenu=submenu,
                    alpha=alpha,
                    size=(1, width),
                )
            else:
                raise TypeError(f"expected Callable or dict, got {type(value)}")

            menu_gadget.add_gadget(menu_item)

        yield menu_gadget


class _MenuButton(Themable, ToggleButtonBehavior, Text):
    def __init__(self, label, menu, group):
        super().__init__(
            size=(1, str_width(label) + 2), group=group, allow_no_selection=True
        )
        self.add_str(f" {label} ")
        self._menu: Menu = menu
        """Menu that the button opens."""

    def _repaint(self):
        if self.button_state != "normal" or self.toggle_state == "on":
            color_pair = self.color_theme.menu_item_hover
        else:
            color_pair = self.color_theme.primary

        self.default_fg_color, self.default_bg_color = color_pair
        self.canvas[["fg_color", "bg_color"]] = color_pair

    def update_theme(self):
        self._repaint()

    def update_down(self):
        self._repaint()

    def update_normal(self):
        self._repaint()

    def update_hover(self):
        self._repaint()
        if self._toggle_groups.get(self.group):
            self.toggle_state = "on"

    def update_on(self):
        self._repaint()

    def update_off(self):
        self._repaint()

    def on_toggle(self):
        if self.toggle_state == "on":
            self._menu.open_menu()
        else:
            self._menu.close_menu()


class MenuBar(GridLayout):
    r"""
    A menu bar.

    A menu bar is constructed with the class method :meth:`from_iterable` from an
    iterable of `(str, MenuDict)`.

    Parameters
    ----------
    close_on_release : bool, default: True
        Whether to close the menu when an item is selected.
    close_on_click : bool, default: True
        Whether to close the menu when a click doesn't collide with it.
    alpha : float, default: 1.0
        Transparency of gadget.
    grid_rows : int, default: 1
        Number of rows.
    grid_columns : int, default: 1
        Number of columns.
    orientation : Orientation, default: "lr-bt"
        The orientation of the grid.
    left_padding : int, default: 0
        Padding on left side of grid.
    right_padding : int, default: 0
        Padding on right side of grid.
    top_padding : int, default: 0
        Padding at the top of grid.
    bottom_padding : int, default: 0
        Padding at the bottom of grid.
    horizontal_spacing : int, default: 0
        Horizontal spacing between children.
    vertical_spacing : int, default: 0
        Vertical spacing between children.
    fg_color : Color | None, default: WHITE
        Foreground color of gadget.
    bg_color : Color | None, default: BLACK
        Background color of gadget.
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
    close_on_release : bool
        Whether to close the menu when an item is selected.
    close_on_click : bool
        Whether to close the menu when a click doesn't collide with it.
    alpha : float
        Transparency of gadget.
    grid_rows : int
        Number of rows.
    grid_columns : int
        Number of columns.
    orientation : Orientation
        The orientation of the grid.
    left_padding : int
        Padding on left side of grid.
    right_padding : int
        Padding on right side of grid.
    top_padding : int
        Padding at the top of grid.
    bottom_padding : int
        Padding at the bottom of grid.
    horizontal_spacing : int
        Horizontal spacing between children.
    vertical_spacing : int
        Vertical spacing between children.
    fg_color : Color | None
        Foreground color of gadget.
    bg_color : Color | None
        Background color of gadget.
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
    open_menu()
        Open menu.
    close_menu()
        Close menu.
    from_dict_of_dicts(...)
        Constructor to create a menu from a dict of dicts. This should be
        default way of constructing menus.
    index_at(row, col)
        Return index of gadget in :attr:`children` at position `row, col` in the grid.
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
        close_on_release: bool = True,
        close_on_click: bool = True,
        alpha: float = 1.0,
        orientation="tb-lr",
        grid_rows: int = 1,
        grid_columns: int = 1,
        padding_left: int = 0,
        padding_right: int = 0,
        padding_top: int = 0,
        padding_bottom: int = 0,
        horizontal_spacing: int = 0,
        vertical_spacing: int = 0,
        size: Size = Size(10, 10),
        pos: Point = Point(0, 0),
        size_hint: SizeHint | None = None,
        pos_hint: PosHint | None = None,
        is_transparent: bool = False,
        is_visible: bool = True,
        is_enabled: bool = True,
    ):
        self._close_on_release = close_on_release
        self._close_on_click = close_on_click
        self._alpha = alpha

        super().__init__(
            orientation=orientation,
            grid_rows=grid_rows,
            grid_columns=grid_columns,
            padding_left=padding_left,
            padding_right=padding_right,
            padding_top=padding_top,
            padding_bottom=padding_bottom,
            horizontal_spacing=horizontal_spacing,
            vertical_spacing=vertical_spacing,
            size=size,
            pos=pos,
            size_hint=size_hint,
            pos_hint=pos_hint,
            is_transparent=is_transparent,
            is_visible=is_visible,
            is_enabled=is_enabled,
        )

    @property
    def close_on_release(self) -> bool:
        """Whether to close the menu when an item is selected."""
        return self._close_on_release

    @close_on_release.setter
    def close_on_release(self, close_on_release: bool):
        self._close_on_release = close_on_release
        button: _MenuButton
        for button in self.children:
            button._menu.close_on_release = close_on_release

    @property
    def close_on_click(self) -> bool:
        """Whether to close the menu when a click doesn't collide with it."""
        return self._close_on_click

    @close_on_click.setter
    def close_on_click(self, close_on_click: bool):
        self._close_on_click = close_on_click
        button: _MenuButton
        for button in self.children:
            button._menu.close_on_click = close_on_click

    @property
    def alpha(self) -> float:
        """Transparancy of gadget."""
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(alpha, 0.0, 1.0)
        button: _MenuButton
        for button in self.children:
            button.alpha = self._alpha
            button._menu.alpha = self._alpha

    def on_transparency(self) -> None:
        """Update gadget after transparency is enabled/disabled."""
        button: _MenuButton
        for button in self.children:
            button.is_transparent = self.is_transparent
            button._menu.is_transparent = self.is_transparent

    def on_key(self, key_event: KeyEvent) -> bool | None:
        """Navigate menu bar with left/right arrow keys."""
        button: _MenuButton
        for i, button in enumerate(self.children):
            if button.toggle_state == "on":
                break
        else:
            return super().on_key(key_event)

        if button._menu.on_key(key_event):
            return True

        if key_event.key == "left":
            i -= 1
        elif key_event.key == "right":
            i += 1
        else:
            return super().on_key(key_event)

        i %= len(self.children)
        self.children[i].toggle_state = "on"
        return True

    @classmethod
    def from_iterable(
        cls,
        iter: Iterable[tuple[str, MenuDict]],
        pos: Point = Point(0, 0),
        close_on_release: bool = True,
        close_on_click: bool = True,
        alpha: float = 1.0,
    ) -> Iterator[MenuBar | Menu]:
        """
        Create and yield a menu bar and menus from an iterable of
        `tuple[str, MenuDict]`.

        Parameters
        ----------
        iter : Iterable[tuple[str, MenuDict]]
            An iterable of `tuple[str, MenuDict]` from which to create the menu bar and
            menus.
        pos : Point, default: Point(0, 0)
            Position of menu.
        close_on_release : bool, default: True
            Whether to close the menu when an item is selected.
        close_on_click : bool, default: True
            Whether to close the menu when a click doesn't collide with it.
        alpha : float, default: 1.0
            Transparency of gadget.

        Yields
        ------
        MenuBar | Menu
            A menu or submenu of the menu bar or the menu bar.
        """
        menus = list(iter)

        menubar = cls(
            close_on_release=close_on_release,
            close_on_click=close_on_click,
            alpha=alpha,
            grid_rows=1,
            grid_columns=len(menus),
            size=(1, sum(str_width(menu_name) + 2 for menu_name, _ in menus)),
            pos=pos,
        )

        y, x = pos
        for menu_name, menu_dict in menus:
            for menu in Menu.from_dict_of_dicts(
                menu_dict,
                pos=(y + 1, x),
                close_on_release=close_on_release,
                close_on_click=close_on_click,
                alpha=alpha,
            ):
                menu.is_enabled = False
                yield menu

            menu._menu_button = _MenuButton(
                menu_name, menu, id(menubar)
            )  # Last menu yielded
            menubar.add_gadget(menu._menu_button)
            x += menu._menu_button.width

        yield menubar
