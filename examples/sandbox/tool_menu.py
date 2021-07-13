import numpy as np

from nurses_2.colors import ColorPair, BLUE
from nurses_2.widgets import Widget
from nurses_2.widgets.button_behavior import ButtonBehavior

from .particles import Element


class ElementButton(ButtonBehavior, Widget):
    def __init__(self, pos, element):
        self.element = element

        super().__init__(
            dim=(2, 4),
            pos=pos,
            default_color=ColorPair(0, 0, 0, *element.COLOR),
        )
        self.down_color = ColorPair(0, 0, 0, *(max(255, 1.2 * c) for c in element.COLOR))

    def update_down(self):
        self.colors[:, :] = self.down_color

    def update_normal(self):
        self.colors[:, :] = self.default_color

    def on_release(self):
        self.parent.parent.particle_type = self.element


class ButtonContainer(Widget):
    def __init__(self):
        nelements = len(Element.registry)

        super().__init__(
            dim=(3 * nelements + 1, 8),
            default_color=ColorPair(0, 0, 0, *BLUE),
        )

        for i, element in enumerate(Element.registry.values()):
            self.add_widget(ElementButton(pos=(3 * i + 1, 2), element=element))
