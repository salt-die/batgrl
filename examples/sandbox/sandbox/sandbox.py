from functools import partial

import numpy as np

from nurses_2.colors import Color, ColorPair
from nurses_2.mouse import MouseButton
from nurses_2.widgets.widget_data_structures import Size
from nurses_2.widgets.widget import Widget, overlapping_region
from nurses_2.widgets.auto_position_behavior import Anchor, AutoPositionBehavior

from .element_buttons import MENU_BACKGROUND_COLOR, ElementDisplay, ButtonContainer
from .particles import Air

@partial(np.vectorize, otypes=[np.uint8, np.uint8, np.uint8])
def particles_to_colors(particle):
    """
    Convert array of particles to array of colors.
    """
    return particle.COLOR


class Sandbox(AutoPositionBehavior, Widget):
    """
    Sandbox widget.
    """
    def __init__(self, dim: Size):
        super().__init__(dim=dim, anchor=Anchor.CENTER, pos_hint=(.5, .5), default_char="▀")

        # Build array of particles -- Initially all Air
        self.world = world = np.full((2 * self.height, self.width), None, dtype=object)
        for y in range(2 * self.height):
            for x in range(self.width):
                world[y, x] = Air(world, (y, x))

        # Add children widgets
        self.display = ElementDisplay(
            dim=(1, 9),
            pos=(1, 0),
            anchor=Anchor.CENTER,
            pos_hint=(None, 0.5),
            default_color=ColorPair(*Air.COLOR, *MENU_BACKGROUND_COLOR),
        )
        self.add_widgets(self.display, ButtonContainer())

        # Press the Stone button setting particle type.
        self.children[1].children[1].on_release()

    def render(self, canvas_view, colors_view, rect):
        # Color of each particle in `self.world` is written into color array.
        colors = np.dstack(particles_to_colors(self.world))
        np.concatenate((colors[::2], colors[1::2]), axis=-1, out=self.colors)

        super().render(canvas_view, colors_view, rect)

    def on_click(self, mouse_event):
        if (
            mouse_event.button != MouseButton.LEFT
            or not self.collides_coords(mouse_event.position)
        ):
            return

        world = self.world
        particle_type = self.particle_type
        y, x = self.absolute_to_relative_coords(mouse_event.position)

        world[2 * y, x].replace(particle_type)
        world[2 * y + 1, x].replace(particle_type)

        return True
