from nurses_2.colors import BLACK, Color, ColorPair
from nurses_2.widgets.behaviors.button_behavior import ButtonBehavior
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

from .particles import Element

MENU_BACKGROUND_COLOR = Color(222, 224, 127)  # Mustard


class ElementButton(ButtonBehavior, TextWidget):
    """
    Button which selects an element when pressed and updates the element display.
    """

    def __init__(self, pos, element):
        self.element = element

        super().__init__(
            size=(2, 4),
            pos=pos,
            default_color_pair=ColorPair.from_colors(BLACK, element.COLOR),
            always_release=True,
        )

        self.down_color = ColorPair.from_colors(
            BLACK,
            Color(*(127 + c // 2 for c in element.COLOR)),
        )

    def update_down(self):
        self.colors[:] = self.down_color

    def update_normal(self):
        self.colors[:] = self.default_color_pair

    def on_release(self):
        element = self.element
        sandbox = self.parent.parent

        sandbox.particle_type = element
        sandbox.display.add_str(f"{element.__name__:^{sandbox.display.width}}")


class ButtonContainer(Widget):
    """
    Container widget of `ElementButton`s.
    """

    def __init__(self):
        nelements = len(Element.all_elements)

        super().__init__(
            size=(3 * nelements + 1, 8),
            background_color_pair=ColorPair.from_colors(
                MENU_BACKGROUND_COLOR, MENU_BACKGROUND_COLOR
            ),
        )

        for i, element in enumerate(Element.all_elements.values()):
            self.add_widget(ElementButton(pos=(3 * i + 1, 2), element=element))

    def on_mouse(self, mouse_event):
        return self.collides_point(mouse_event.position)
