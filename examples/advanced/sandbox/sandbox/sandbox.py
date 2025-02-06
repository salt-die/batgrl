from functools import partial

import numpy as np
from batgrl.colors import ABLACK
from batgrl.gadgets.graphics import Graphics, Size, scale_geometry
from batgrl.gadgets.text import Text, new_cell

from .element_buttons import MENU_BACKGROUND_COLOR, ButtonContainer
from .particles import Air


@partial(np.vectorize, otypes=[np.uint8, np.uint8, np.uint8])
def particles_to_colors(particle):
    """Convert array of particles to array of colors."""
    return particle.COLOR


class Sandbox(Graphics):
    """Sandbox gadget."""

    def __init__(self, size: Size):
        super().__init__(
            size=size,
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            default_color=ABLACK,
            blitter="full",
        )

    def on_add(self):
        super().on_add()
        # Build array of particles -- Initially all Air
        h, w = scale_geometry(self._blitter, self._size)
        self.world = world = np.full((h, w), None, dtype=object)
        for y in range(h):
            for x in range(w):
                world[y, x] = Air(world, (y, x))

        self.display = Text(
            size=(1, 9),
            pos=(1, 0),
            pos_hint={"x_hint": 0.5},
            default_cell=new_cell(fg_color=Air.COLOR, bg_color=MENU_BACKGROUND_COLOR),
        )
        self.add_gadgets(self.display, ButtonContainer())

        # Press the Stone button setting particle type.
        self.children[1].children[1].on_release()

    def on_remove(self):
        super().on_remove()
        for particle in self.world.flatten():
            particle.sleep()

    def _render(self, cells, graphics, kind):
        # Color of each particle in `self.world` is written into color array.
        self.texture[..., :3] = np.dstack(particles_to_colors(self.world))
        super()._render(cells, graphics, kind)

    def on_mouse(self, mouse_event):
        if mouse_event.button != "left" or not self.collides_point(mouse_event.pos):
            return

        world = self.world
        particle_type = self.particle_type
        y, x = scale_geometry(self._blitter, self.to_local(mouse_event.pos))
        h, w = scale_geometry(self._blitter, Size(1, 1))
        for i in range(h):
            for j in range(w):
                world[y + i, x + j].replace(particle_type)
        return True
