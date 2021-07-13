from nurses_2.colors import ColorPair
from nurses_2.widgets import Widget
from nurses_2.widgets.button_behavior import ButtonBehavior

from .constants import *
from .particles import Element


class ElementButton(ButtonBehavior, Widget):
    def __init__(self, pos, element):
        self.element = element

        super().__init__(
            dim=(2, 4),
            pos=pos,
            default_color=ColorPair(0, 0, 0, *element.COLOR),
            always_release=True,
        )
        self.down_color = ColorPair(*(min(255, int(1.3 * c)) for c in self.default_color))

    def update_down(self):
        self.colors[:, :] = self.down_color

    def update_normal(self):
        self.colors[:, :] = self.default_color

    def on_release(self):
        self.parent.parent.particle_type = self.element


class ButtonContainer(Widget):
    def __init__(self):
        nelements = len(Element.all_elements)

        super().__init__(
            dim=(3 * nelements + 1, 8),
            default_color=ColorPair(0, 0, 0, *MENU_BACKGROUND_COLOR),
        )

        for i, element in enumerate(Element.all_elements.values()):
            self.add_widget(ElementButton(pos=(3 * i + 1, 2), element=element))

    def on_click(self, mouse_event):
        if self.collides_coords(mouse_event.position):
            return True
