from inspect import signature
from typing import Callable, Optional

from wcwidth import wcswidth

from ..io import MouseEventType
from .behaviors.themable import Themable
from .behaviors.toggle_button_behavior import ToggleButtonBehavior, ToggleState, ButtonState
from .grid_layout import GridLayout, Orientation
from .text_widget import TextWidget
from .widget import Widget, Anchor, Point

__all__ = (
    "Menu",
    "MenuItem",
)

MenuDict = dict[tuple[str, str], Callable[[], None] | Callable[[ToggleState], None] | "MenuDict"]
NESTED_SUFFIX = " ▶"
CHECK_OFF = "□"
CHECK_ON = "▣"

def nargs(callable: Callable):
    """
    Return the number of arguments of `callable`.
    """
    return len(signature(callable).parameters)


class MenuItem(Themable, ToggleButtonBehavior, Widget):
    def __init__(
        self,
        left_label: str="",
        right_label: str="",
        item_disabled: bool=False,
        item_callback: Callable[[], None]=lambda: None,
        submenu: Optional["Menu"]=None,
        **kwargs
    ):
        self.normal_color_pair = (0, ) * 6  # Temporary assignment

        self._item_disabled = item_disabled

        self.left_label = TextWidget(size=(1, wcswidth(left_label)))
        self.left_label.add_text(left_label)

        self.right_label = TextWidget(
            size=(1, wcswidth(right_label)),
            pos_hint=(None, 1.0),
            anchor=Anchor.RIGHT_CENTER,
        )
        self.right_label.add_text(right_label)

        self.submenu = submenu

        super().__init__(**kwargs)

        self.add_widgets(self.left_label, self.right_label)

        self.item_callback = item_callback
        self.update_off()
        self.update_theme()

    @property
    def item_disabled(self) -> bool:
        return self._item_disabled

    @item_disabled.setter
    def item_disabled(self, item_disabled: bool):
        self._item_disabled = item_disabled
        self.update_theme()

    def update_theme(self):
        ct = self.color_theme

        self.normal_color_pair = ct.primary_color_pair
        self.hover_color_pair = ct.primary_light_color_pair
        self.disabled_color_pair = ct.primary_dark_color_pair

        if self.state is ButtonState.NORMAL:
            self.update_normal()
        else:
            self.update_hover()

    def _update_color_pair(self, color):
        if self.item_disabled:
            color = self.disabled_color_pair

        self.background_color_pair = color
        self.left_label.colors[:] = color
        self.right_label.colors[:] = color

    def update_hover(self):
        self._update_color_pair(self.hover_color_pair)

        index = self.parent.children.index(self)
        if self.parent._current_selection not in (-1, index):
            self.parent.close_submenus()
            self.parent.children[self.parent._current_selection]._normal()

        self.parent._current_selection = index

        if self.submenu is not None:
            self.submenu.open_menu()

    def update_normal(self):
        if self.parent is None:
            self._update_color_pair(self.normal_color_pair)
            return

        if self.submenu is None or not self.submenu.is_enabled:
            pass
        elif not self.submenu.collides_point(self._last_mouse_pos):
            self.submenu.close_menu()
        else:
            return

        self._update_color_pair(self.normal_color_pair)
        if self.parent._current_selection == self.parent.children.index(self):
            self.parent._current_selection = -1

    def on_click(self, mouse_event):
        self._last_mouse_pos = mouse_event.position
        return super().on_click(mouse_event)

    def on_release(self):
        if self.item_disabled:
            return

        if self.submenu is not None:
            self.submenu.open_menu()
        elif nargs(self.item_callback) == 0:
            self.item_callback()

            if self.parent.close_on_release:
                self.parent.close_parents()

    def update_off(self):
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas[0, 1] = CHECK_OFF

    def update_on(self):
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.left_label.canvas[0, 1] = CHECK_ON

    def on_toggle(self):
        if self.item_callback is not None and nargs(self.item_callback) == 1:
            self.item_callback(self.toggle_state)


class Menu(GridLayout):
    """
    A menu widget.

    Menus are meant to be constructed with the class method `from_dict_of_dicts`.
    The each key of the dict should be a tuple of two strings for left and right labels and
    each value should be either a callable with no arguments for a normal menu item, a
    callable with one argument for a toggle menu item (the argument will be the state of the
    toggle button, `ToggleState`) or a dict (for a submenu).

    See Also
    --------
    https://github.com/salt-die/nurses_2/blob/main/examples/menu.py

    Parameters
    ----------
    close_on_release : bool, default: True
        If true, close the menu when an item is selected.
    close_on_click : bool, default: True
        If true, close the menu when a click doesn't collide with it.
    """
    def __init__(
        self,
        close_on_release: bool=True,
        close_on_click: bool=True,
        orientation=Orientation.TB_LR,
        **kwargs
    ):
        super().__init__(orientation=orientation, **kwargs)

        self.close_on_release = close_on_release
        self.close_on_click = close_on_click

        self._parent_menu = None
        self._current_selection = -1
        self._submenus = [ ]

    def open_menu(self):
        self.is_enabled = True

    def close_menu(self):
        self.is_enabled = False
        self._current_selection = -1

        self.close_submenus()

        for child in self.children:
            child._normal()

    def close_submenus(self):
        for menu in self._submenus:
            menu.close_menu()

    def close_parents(self):
        if self._parent_menu is not None:
            self._parent_menu.close_parents()
        else:
            self.close_menu()

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and self.close_on_click
            and not (
                self.collides_point(mouse_event.position)
                or any(submenu.collides_point(mouse_event.position) for submenu in self._submenus)
            )
        ):
            self.close_menu()
            return False

        return super().on_click(mouse_event)

    def on_press(self, key_press_event):
        for submenu in self._submenus:
            if submenu.is_enabled:
                if submenu.on_press(key_press_event):
                    return True
                else:
                    break

        match key_press_event.key:
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
                if (
                    self._current_selection != -1
                    and (
                        (submenu := self.children[self._current_selection].submenu)
                        and submenu.is_enabled
                    )
                ):
                        submenu.close_menu()
                        return True

            case "right":
                if (
                    self._current_selection != -1
                    and (
                        (submenu := self.children[self._current_selection].submenu)
                        and not submenu.is_enabled
                    )
                ):
                    submenu.open_menu()
                    if submenu.children:
                        submenu.children[0]._hover()
                        submenu.close_submenus()
                    return True

            case "enter":
                if self._current_selection != -1 and (child := self.children[self._current_selection]).submenu is None:
                    if (n := nargs(child.item_callback)) == 0:
                        child.on_release()
                    elif n == 1:
                        child._down()
                    return True

        return super().on_press(key_press_event)

    @classmethod
    def from_dict_of_dicts(
        cls,
        menu: MenuDict,
        pos: Point=Point(0, 0),
        close_on_release=True,
        close_on_click=True,
    ):
        """
        Create and yield menus from a dict of dicts. Callables should either have no arguments
        for a normal menu item, or one argument for a toggle menu item.

        See Also
        --------
        https://github.com/salt-die/nurses_2/blob/main/examples/menu.py

        Parameters
        ----------
        menu : MenuDict
            The menu as a dict of dicts.
        """
        height = len(menu)
        width = max(
            (
                wcswidth(right_label)
                + wcswidth(left_label)
                + 7
                + isinstance(callable_or_dict, dict) * 2
            ) for (right_label, left_label), callable_or_dict in menu.items()
        )
        menu_widget = cls(
            grid_rows=height,
            grid_columns=1,
            size=(height, width),
            pos=pos,
            close_on_release=close_on_release,
            close_on_click=close_on_click,
        )

        y, x = pos
        for i, ((left_label, right_label), callable_or_dict) in enumerate(menu.items()):
            if not isinstance(callable_or_dict, Callable):
                for nested in Menu.from_dict_of_dicts(
                    callable_or_dict,
                    pos=(y + i, x + width),
                    close_on_release=close_on_release,
                    close_on_click=close_on_click,
                ):
                    nested._parent_menu = menu_widget
                    nested.is_enabled = False
                    menu_widget._submenus.append(nested)

                    yield nested

                right_label += NESTED_SUFFIX

                menu_item = MenuItem(
                    left_label=f"   {left_label}",
                    right_label=f"{right_label} ",
                    submenu=nested,
                    size=(1, width),
                )

            else:
                menu_item = MenuItem(
                    left_label=f"   {left_label}",
                    right_label=f"{right_label} ",
                    item_callback=callable_or_dict,
                    size=(1, width),
                )

            menu_widget.add_widget(menu_item)

        yield menu_widget
