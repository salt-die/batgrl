from typing import Callable, Optional

from wcwidth import wcswidth

from ..io import MouseEventType
from .behaviors.button_behavior import ButtonBehavior, ButtonState
from .behaviors.themable import Themable
from .grid_layout import GridLayout, Orientation
from .text_widget import TextWidget
from .widget import Widget, Anchor, Point

__all__ = "Menu",

MenuDict = dict[tuple[str, str], Callable | "MenuDict"]
NESTED_SUFFIX = " ▶"


class MenuItem(Themable, ButtonBehavior, Widget):
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

        self.item_disabled = item_disabled

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
        self.parent.close_submenus()

        if self.submenu is not None:
            self.submenu.open_menu()

    def update_normal(self):
        self._update_color_pair(self.normal_color_pair)

    def on_release(self):
        if self.submenu is not None:
            self.submenu.open_menu()
        else:
            self.item_callback()

            if self.parent.close_on_release:
                self.parent.close_parents()


class Menu(GridLayout):
    """
    A menu widget. Create menus quickly with the `from_dict_of_dicts` method.

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
        self._submenus = [ ]

    def open_menu(self):
        self.is_enabled = True

    def close_submenus(self):
        for menu in self._submenus:
            menu.is_enabled = False

    def close_menu(self):
        self.is_enabled = False
        self.close_submenus()

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

        return super().on_click(mouse_event)

    @classmethod
    def from_dict_of_dicts(
        cls,
        menu: MenuDict,
        pos: Point=Point(0, 0),
        close_on_release=True,
        close_on_click=True,
    ):
        """
        Create and yield menus from a dict of dicts.

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
                + 5
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
                    left_label=f" {left_label}",
                    right_label=f"{right_label} ",
                    submenu=nested,
                    size=(1, width),
                )

            else:
                menu_item = MenuItem(
                    left_label=f" {left_label}",
                    right_label=f"{right_label} ",
                    item_callback=callable_or_dict,
                    size=(1, width),
                )

            menu_widget.add_widget(menu_item)

        yield menu_widget
