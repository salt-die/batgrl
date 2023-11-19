"""A menu gadget."""
from collections.abc import Callable, Hashable, Iterable, Iterator
from inspect import signature
from typing import Optional, Union

from numpy.typing import NDArray
from wcwidth import wcswidth

from ..colors import ColorPair
from ..io import MouseEventType
from .behaviors.themable import Themable
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
from .grid_layout import GridLayout
from .text import Text

__all__ = [
    "Menu",
    "MenuBar",
    "MenuDict",
    "MenuItem",
    "Point",
    "PosHint",
    "PosHintDict",
    "Size",
    "SizeHint",
    "SizeHintDict",
]

ItemCallback = Callable[[], None] | Callable[[ToggleState], None]
MenuDict = dict[tuple[str, str], Union[ItemCallback, "MenuDict"]]
NESTED_SUFFIX = " ▶"
CHECK_OFF = "□"
CHECK_ON = "▣"


def nargs(callable: Callable) -> int:
    """Return the number of arguments of `callable`."""
    return len(signature(callable).parameters)


class MenuItem(Themable, ToggleButtonBehavior, Gadget):
    r"""
    A single item in a menu gadget. This should normally only be
    instantiated by :meth:`Menu.from_dict_of_dicts`.

    Parameters
    ----------
    left_label : str, default: ""
        Left label of menu item.
    right_label : str, default: ""
        Right label of menu item.
    item_disabled : bool, default: False
        If true, item will not be selectable in menu.
    item_callback : ItemCallback, default: lambda: None
        Callback when item is selected. For toggle items, the callable should have a
        single argument that will be the current state of the item.
    group : None | Hashable, default: None
        If a group is provided, only one button in a group can be in the "on" state.
    allow_no_selection : bool, default: False
        If a group is provided, setting this to true allows no selection, i.e.,
        every button can be in the "off" state.
    toggle_state : ToggleState, default: ToggleState.OFF
        Initial toggle state of button.
    always_release : bool, default: False
        Whether a mouse up event outside the button will trigger it.
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
    left_label : str
        Left label of menu item.
    right_label : str
        Right label of menu item.
    item_disabled : bool
        If true, item will not be selectable in menu.
    item_callback : ItemCallback
        Callback when item is selected. For toggle items, the callable should have a
        single argument that will be the current state of the item.
    submenu: Menu | None
        If provided, menu item will open submenu on hover.
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
    update_off():
        Paint the "off" state.
    update_on():
        Paint the "on" state.
    on_toggle():
        Update gadget on toggle state change.
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
    """  # noqa: E501

    def __init__(
        self,
        *,
        left_label: str = "",
        right_label: str = "",
        item_disabled: bool = False,
        item_callback: ItemCallback = lambda: None,
        submenu: Optional["Menu"] = None,
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
        background_char: NDArray[Char] | str | None = None,
        background_color_pair: ColorPair | None = None,
    ):
        self.normal_color_pair = (0,) * 6  # Temporary assignment

        self._item_disabled = item_disabled

        self.left_label = Text(size=(1, wcswidth(left_label)))
        self.left_label.add_str(left_label)

        self.right_label = Text(
            size=(1, wcswidth(right_label)),
            pos_hint={"x_hint": 1.0, "anchor": "right"},
        )
        self.right_label.add_str(right_label)

        self.submenu = submenu

        super().__init__(
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.add_gadgets(self.left_label, self.right_label)

        self.item_callback = item_callback
        self.update_off()

    def _repaint(self):
        if self.item_disabled:
            color = self.color_theme.menu_item_disabled
        elif self.state is ButtonState.NORMAL:
            color = self.color_theme.primary
        elif self.state is ButtonState.HOVER or self.state is ButtonState.DOWN:
            color = self.color_theme.menu_item_hover

        self.background_color_pair = color
        self.left_label.colors[:] = color
        self.right_label.colors[:] = color

    @property
    def item_disabled(self) -> bool:
        """If true, item will not be selectable in menu."""
        return self._item_disabled

    @item_disabled.setter
    def item_disabled(self, item_disabled: bool):
        self._item_disabled = item_disabled
        self._repaint()

    def update_theme(self):
        """Paint the gadget with current theme."""
        self._repaint()

    def update_hover(self):
        """Update parent menu and submenu on hover state."""
        self._repaint()

        index = self.parent.children.index(self)
        if self.parent._current_selection not in {-1, index}:
            self.parent.close_submenus()
            if self.parent._current_selection != -1:
                self.parent.children[self.parent._current_selection]._normal()

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

    def on_mouse(self, mouse_event):
        """Save last mouse position."""
        self._last_mouse_pos = mouse_event.position
        return super().on_mouse(mouse_event)

    def on_release(self):
        """Open submenu or call item callback on release."""
        if self.item_disabled:
            return

        if self.submenu is not None:
            self.submenu.open_menu()
        elif nargs(self.item_callback) == 0:
            self.item_callback()

            if self.parent.close_on_release:
                self.parent.close_parents()

    def update_off(self):
        """Paint the off state."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas["char"][0, 1] = CHECK_OFF

    def update_on(self):
        """Paint the on state."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas["char"][0, 1] = CHECK_ON

    def on_toggle(self):
        """Call item callback on toggle state change."""
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.item_callback(self.toggle_state)


class Menu(GridLayout):
    r"""
    A menu gadget.

    Menus are meant to be constructed with the class method :meth:`from_dict_of_dicts`.
    Each key of the dict should be a tuple of two strings for left and right labels and
    each value should be either a callable with no arguments for a normal menu item, a
    callable with one argument for a toggle menu item (the argument will be
    :attr:`batgrl.gadgets.behaviors.toggle_button_behavior.ToggleButtonBehavior.toggle_state`
    of the menu item), or a dict (for a submenu).

    Once opened, a menu can be navigated with the mouse or arrow keys.

    Parameters
    ----------
    close_on_release : bool, default: True
        If true, close the menu when an item is selected.
    close_on_click : bool, default: True
        If true, close the menu when a click doesn't collide with it.
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
    close_on_release : bool
        If true, close the menu when an item is selected.
    close_on_click : bool
        If true, close the menu when a click doesn't collide with it.
    minimum_grid_size : Size
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
    open_menu():
        Open menu.
    close_menu():
        Close menu.
    from_dict_of_dicts(...):
        Constructor to create a menu from a dict of dicts. This should be
        default way of constructing menus.
    index_at(row, col):
        Return index of gadget in :attr:`children` at position `row, col` in the grid.
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
        close_on_release: bool = True,
        close_on_click: bool = True,
        orientation="tb-lr",
        grid_rows: int = 1,
        grid_columns: int = 1,
        padding_left: int = 0,
        padding_right: int = 0,
        padding_top: int = 0,
        padding_bottom: int = 0,
        horizontal_spacing: int = 0,
        vertical_spacing: int = 0,
        size=Size(10, 10),
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
            background_char=background_char,
            background_color_pair=background_color_pair,
        )

        self.close_on_release = close_on_release
        self.close_on_click = close_on_click

        self._parent_menu = None
        self._current_selection = -1
        self._submenus = []
        self._menu_button = None

    def open_menu(self):
        """Open the menu."""
        self.is_enabled = True

    def close_menu(self):
        """Close the menu."""
        if (
            self._menu_button is not None
            and self._menu_button.toggle_state is ToggleState.ON
        ):
            self._menu_button.toggle_state = ToggleState.OFF
        else:
            self.is_enabled = False
            self._current_selection = -1
            self.close_submenus()

            for child in self.children:
                child._normal()

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
            mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and self.close_on_click
            and not (
                self.collides_point(mouse_event.position)
                or any(
                    submenu.collides_point(mouse_event.position)
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

        match key_event.key:
            case "up":
                i = self._current_selection

                if i == -1:
                    i = len(self.children) - 1
                else:
                    i = self._current_selection
                    self.children[i]._normal()
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

            case "down":
                i = self._current_selection

                if i == -1:
                    i = 0
                else:
                    self.children[i]._normal()
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

            case "left":
                if self._current_selection != -1 and (
                    (submenu := self.children[self._current_selection].submenu)
                    and submenu.is_enabled
                ):
                    submenu.close_menu()
                    return True

            case "right":
                if self._current_selection != -1 and (
                    (submenu := self.children[self._current_selection].submenu)
                    and not submenu.is_enabled
                ):
                    submenu.open_menu()
                    if submenu.children:
                        submenu.children[0]._hover()
                        submenu.close_submenus()
                    return True

            case "enter":
                if (
                    self._current_selection != -1
                    and (child := self.children[self._current_selection]).submenu
                    is None
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
    ) -> Iterator["Menu"]:
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
            If true, close the menu when an item is selected.
        close_on_click : bool, default: True
            If true, close the menu when a click doesn't collide with it.

        Yields
        ------
        Menu
            The menu or one of its submenus.
        """
        height = len(menu)
        width = max(
            (
                wcswidth(right_label)
                + wcswidth(left_label)
                + 7
                + isinstance(callable_or_dict, dict) * 2
            )
            for (right_label, left_label), callable_or_dict in menu.items()
        )
        menu_gadget = cls(
            grid_rows=height,
            grid_columns=1,
            size=(height, width),
            pos=pos,
            close_on_release=close_on_release,
            close_on_click=close_on_click,
        )

        y, x = pos
        for i, ((left_label, right_label), callable_or_dict) in enumerate(menu.items()):
            match callable_or_dict:
                case Callable():
                    menu_item = MenuItem(
                        left_label=f"   {left_label}",
                        right_label=f"{right_label} ",
                        item_callback=callable_or_dict,
                        size=(1, width),
                    )
                case dict():
                    for nested in Menu.from_dict_of_dicts(
                        callable_or_dict,
                        pos=(y + i, x + width),
                        close_on_release=close_on_release,
                        close_on_click=close_on_click,
                    ):
                        nested._parent_menu = menu_gadget
                        nested.is_enabled = False
                        menu_gadget._submenus.append(nested)

                        yield nested

                    menu_item = MenuItem(
                        left_label=f"   {left_label}",
                        right_label=f"{right_label}{NESTED_SUFFIX} ",
                        submenu=nested,
                        size=(1, width),
                    )
                case _:
                    raise TypeError(
                        f"expected Callable or dict, got {type(callable_or_dict)}"
                    )

            menu_gadget.add_gadget(menu_item)

        yield menu_gadget


class _MenuButton(Themable, ToggleButtonBehavior, Text):
    def __init__(self, label, menu, group):
        super().__init__(
            size=(1, wcswidth(label) + 2), group=group, allow_no_selection=True
        )
        self.add_str(f" {label} ")
        self._menu = menu

    def _repaint(self):
        if self.state is not ButtonState.NORMAL or self.toggle_state is ToggleState.ON:
            color_pair = self.color_theme.menu_item_hover
        else:
            color_pair = self.color_theme.primary

        self.colors[:] = color_pair
        self.default_color_pair = color_pair

    def update_theme(self):
        self._repaint()

    def update_down(self):
        self._repaint()

    def update_normal(self):
        self._repaint()

    def update_hover(self):
        self._repaint()
        if self._toggle_groups.get(self.group):
            self.toggle_state = ToggleState.ON

    def update_on(self):
        self._repaint()

    def update_off(self):
        self._repaint()

    def on_toggle(self):
        if self.toggle_state is ToggleState.ON:
            self._menu.open_menu()
        else:
            self._menu.close_menu()


class MenuBar(GridLayout):
    r"""
    A menu bar.

    A menu bar is meant to be constructed with the class method :meth:`from_iterable`.
    The iterable should be pairs of `(str, MenuDict)` where `MenuDict` is the type
    used for `Menu.from_dict_of_dicts`.

    Parameters
    ----------
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
    close_on_release : bool
        If true, close the menu when an item is selected.
    close_on_click : bool
        If true, close the menu when a click doesn't collide with it.
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
    open_menu():
        Open menu.
    close_menu():
        Close menu.
    from_dict_of_dicts(...):
        Constructor to create a menu from a dict of dicts. This should be
        default way of constructing menus.
    index_at(row, col):
        Return index of gadget in :attr:`children` at position `row, col` in the grid.
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

    @classmethod
    def from_iterable(
        cls,
        iter: Iterable[tuple[str, MenuDict]],
        pos: Point = Point(0, 0),
        close_on_release: bool = True,
        close_on_click: bool = True,
    ) -> Iterator[Union[Menu, "MenuBar"]]:
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
            If true, close the menu when an item is selected.
        close_on_click : bool, default: True
            If true, close the menu when a click doesn't collide with it.

        Yields
        ------
        Menu | "MenuBar"
            A menu or submenu of the menu bar or the menu bar.
        """
        menus = list(iter)

        menubar = cls(
            grid_rows=1,
            grid_columns=len(menus),
            size=(1, sum(wcswidth(menu_name) + 2 for menu_name, _ in menus)),
            pos=pos,
        )

        y, x = pos
        for menu_name, menu_dict in menus:
            for menu in Menu.from_dict_of_dicts(
                menu_dict,
                pos=(y + 1, x),
                close_on_release=close_on_release,
                close_on_click=close_on_click,
            ):
                menu.is_enabled = False
                yield menu

            menu._menu_button = _MenuButton(
                menu_name, menu, id(menubar)
            )  # Last menu yielded
            menubar.add_gadget(menu._menu_button)
            x += menu._menu_button.width

        yield menubar
