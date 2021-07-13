import numpy as np

from nurses_2.colors import Color
from nurses_2.mouse import MouseButton
from nurses_2.widgets import Widget
from nurses_2.widgets.auto_position_behavior import Anchor, AutoPositionBehavior

from .constants import *
from .particles.sand import Sand
from .particles.stone import Stone
from .particles.water import Water


BACKGROUND_COLOR = Color(25, 25, 25)

@np.vectorize
def particles_to_colors(particle):
    if particle is None:
        return BACKGROUND_COLOR
    return particle.COLOR


class Sandbox(AutoPositionBehavior, Widget):
    def __init__(self, *args, **kwargs):
        kwargs.pop('anchor', None)
        kwargs.pop('pos_hint', None)
        super().__init__(*args, anchor=Anchor.CENTER, pos_hint=(.5, .5), **kwargs)
        del self.canvas
        del self.colors

        self.world = np.full((self.height * 2, self.width), None, dtype=object)

    def render(self, canvas_view, colors_view, rect):
        colors = np.dstack(particles_to_colors(self.world))
        colors = np.concatenate((colors[::2], colors[1::2]), axis=-1)

        t, l, b, r, _, _ = rect

        canvas_view[:] = "▀"
        colors_view[:] = colors[t:b, l:r]

    def on_click(self, mouse_event):
        if (
            mouse_event.button is MouseButton.NO_BUTTON
            or not self.collides_coords(mouse_event.position)
        ):
            return

        world = self.world
        y, x = self.absolute_to_relative_coords(mouse_event.position)
        upper = 2 * y, x
        lower = 2 * y + 1, x

        if mouse_event.button == MouseButton.LEFT:
            new_particle = Sand
        elif mouse_event.button == MouseButton.RIGHT:
            new_particle = Stone
        else:  # Middle button
            new_particle = Water

        if world[upper] is None:
            new_particle(world, upper)

        if world[lower] is None:
            new_particle(world, lower)
