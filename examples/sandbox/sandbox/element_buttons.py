from nurses_2.colors import ColorPair, Color
from nurses_2.widgets import Widget
from nurses_2.widgets.button_behavior import ButtonBehavior

from .particles import Element

MENU_BACKGROUND_COLOR = Color(222, 224, 127)  # Mustard


class ElementButton(ButtonBehavior, Widget):
    def __init__(self, pos, element):
        self.element = element

        super().__init__(
            dim=(2, 4),
            pos=pos,
            default_color=ColorPair(0, 0, 0, *element.COLOR),
            always_release=True,
        )
        self.down_color = ColorPair(*(int(127 + .5 * c) for c in self.default_color))

    def update_down(self):
        self.colors[:, :] = self.down_color

    def update_normal(self):
        self.colors[:, :] = self.default_color

    def on_release(self):
        element = self.element
        sandbox = self.parent.parent

        sandbox.particle_type = element
        sandbox.display.add_text(f"{element.__name__:^9}", 0, 0)


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
