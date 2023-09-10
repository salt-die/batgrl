from functools import partial

import numpy as np

from nurses_2.colors import ABLACK, ColorPair
from nurses_2.io import MouseButton
from nurses_2.widgets.graphic_widget import Anchor, GraphicWidget, Size
from nurses_2.widgets.text_widget import TextWidget

from .element_buttons import MENU_BACKGROUND_COLOR, ButtonContainer
from .particles import Air


@partial(np.vectorize, otypes=[np.uint8, np.uint8, np.uint8])
def particles_to_colors(particle):
    """
    Convert array of particles to array of colors.
    """
    return particle.COLOR


class Sandbox(GraphicWidget):
    """
    Sandbox widget.
    """

    def __init__(self, size: Size):
        super().__init__(
            size=size, anchor=Anchor.CENTER, pos_hint=(0.5, 0.5), default_color=ABLACK
        )

    def on_add(self):
        super().on_add()
        # Build array of particles -- Initially all Air
        self.world = world = np.full((2 * self.height, self.width), None, dtype=object)
        for y in range(2 * self.height):
            for x in range(self.width):
                world[y, x] = Air(world, (y, x))

        self.display = TextWidget(
            size=(1, 9),
            pos=(1, 0),
            anchor=Anchor.CENTER,
            pos_hint=(None, 0.5),
            default_color_pair=ColorPair.from_colors(Air.COLOR, MENU_BACKGROUND_COLOR),
        )
        self.add_widgets(self.display, ButtonContainer())

        # Press the Stone button setting particle type.
        self.children[1].children[1].on_release()

    def on_remove(self):
        super().on_remove()
        for particle in self.world.flatten():
            particle.sleep()

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        # Color of each particle in `self.world` is written into color array.
        self.texture[..., :3] = np.dstack(particles_to_colors(self.world))
        super().render(canvas_view, colors_view, source)

    def on_mouse(self, mouse_event):
        if mouse_event.button != MouseButton.LEFT or not self.collides_point(
            mouse_event.position
        ):
            return

        world = self.world
        particle_type = self.particle_type
        y, x = self.to_local(mouse_event.position)

        world[2 * y, x].replace(particle_type)
        world[2 * y + 1, x].replace(particle_type)

        return True
