import numpy as np

from nurses_2.colors import Color
from nurses_2.mouse import MouseButton
from nurses_2.widgets.widget import Widget, overlapping_region
from nurses_2.widgets.auto_position_behavior import Anchor, AutoPositionBehavior

from .particles import Air
from .tool_menu import ButtonContainer

@np.vectorize
def particles_to_colors(particle):
    return particle.COLOR


class Sandbox(AutoPositionBehavior, Widget):
    def __init__(self, *args, **kwargs):
        kwargs.pop('anchor', None)
        kwargs.pop('pos_hint', None)
        super().__init__(*args, anchor=Anchor.CENTER, pos_hint=(.5, .5), **kwargs)
        del self.canvas
        del self.colors

        self.world = world = np.full((2 * self.height, self.width), None, dtype=object)
        for y in range(2 * self.height):
            for x in range(self.width):
                world[y, x] = Air(world, (y, x))

        self.add_widget(ButtonContainer())
        # Grab the initial particle type from the tool menu.
        self.particle_type = self.children[0].children[1].element

    def render(self, canvas_view, colors_view, rect):
        colors = np.dstack(particles_to_colors(self.world))
        colors = np.concatenate((colors[::2], colors[1::2]), axis=-1)

        t, l, b, r, _, _ = rect

        canvas_view[:] = "▀"
        colors_view[:] = colors[t:b, l:r]

        for child in self.children:
            if region := overlapping_region(rect, child):
                dest_slice, child_rect = region
                child.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)

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
            world[upper].sleep()
            self.particle_type(world, upper)
            world[upper].wake_neighbors()

            world[lower].sleep()
            self.particle_type(world, lower)
            world[lower].wake_neighbors()
