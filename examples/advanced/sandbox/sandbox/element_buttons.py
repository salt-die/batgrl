from batgrl.colors import BLACK, WHITE, Color, lerp_colors
from batgrl.gadgets.behaviors.button_behavior import ButtonBehavior
from batgrl.gadgets.pane import Pane
from batgrl.gadgets.text import Text, cell

from .particles import Element

MENU_BACKGROUND_COLOR = Color(222, 224, 127)  # Mustard


class ElementButton(ButtonBehavior, Text):
    """Button which selects an element when pressed and updates the element display."""

    def __init__(self, pos, element):
        self.element = element
        self.down_color = lerp_colors(WHITE, element.COLOR, 0.5)
        super().__init__(
            size=(2, 4),
            pos=pos,
            default_cell=cell(fg_color=BLACK, bg_color=element.COLOR),
            always_release=True,
        )

    def update_down(self):
        self.canvas["bg_color"] = self.down_color

    def update_normal(self):
        self.canvas["bg_color"] = self.default_bg_color

    def on_release(self):
        element = self.element
        sandbox = self.parent.parent

        sandbox.particle_type = element
        sandbox.display.add_str(f"{element.__name__:^{sandbox.display.width}}")


class ButtonContainer(Pane):
    """Container gadget of `ElementButton`s."""

    def __init__(self):
        nelements = len(Element.all_elements)
        super().__init__(size=(3 * nelements + 1, 8), bg_color=MENU_BACKGROUND_COLOR)

        for i, element in enumerate(Element.all_elements.values()):
            self.add_gadget(ElementButton(pos=(3 * i + 1, 2), element=element))

    def on_mouse(self, mouse_event):
        return self.collides_point(mouse_event.position)
