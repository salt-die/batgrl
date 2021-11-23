"""
Stable fluid simulation. WIP
"""
from itertools import cycle

import numpy as np

from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.ndimage.filters import convolve

from nurses_2.colors import rainbow_gradient
from nurses_2.io import MouseEvent, MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget

DIF_KERNEL = np.array([-.5, 0.0, .5])
GRAD_KERNEL = np.array([-1.0, 0.0, 1.0])
POISSON_KERNEL = np.array([
    [0.0, .25, 0.0],
    [.25, 0.0, .25],
    [0.0, .25, 0.0],
])
CURL = 1.0
DISSIPATION = 1.01
POKE_RADIUS = 2.0
RAINBOW_COLORS = cycle(rainbow_gradient(100))


class StableFluid(GraphicWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(self.size)

    def resize(self, size: Size):
        super().resize(size)

        h, w = self.texture.shape

        self.dye = np.zeros((3, h, w))
        self.indices = np.indices((h, w))
        self.velocity = np.zeros((2, h, w))

    def _init_inflow(self):
        """
        Init constant velocity field.
        """

    def on_click(self, mouse_event: MouseEvent):
        """
        Add dye on click.
        """
        if (
            mouse_event.button is MouseButton.NO_BUTTON
            or not self.collides_coords(mouse_event.position)
        ):
            return False

        y, x = self.absolute_to_relative_coords(mouse_event.position)
        y *= 2

    def render(self, canvas_view, colors_view, rect: Rect):
        vy, vx = velocity = self.velocity
        dye = self.dye

        # Vorticity
        ###########
        div_y = convolve(vy, DIF_KERNEL[None], mode="wrap")
        div_x = convolve(vx, DIF_KERNEL[:, None], mode="wrap")

        curl = div_y - div_x

        vort_y = convolve(curl, DIF_KERNEL[None], mode="wrap")
        vort_x = convolve(curl, DIF_KERNEL[:, None], mode="wrap")

        vorticity = np.stack((vort_y, vort_x))
        vorticity /= np.linalg.norm(vorticity, axis=0) + .00001
        vorticity *= curl * CURL
        vorticity[0] *= -1

        velocity += vorticity
        # np.clip(velocity, -100, 100)  # May need to limit velocity.

        # Project
        #########
        vy -= convolve(vy, DIF_KERNEL[None], mode="wrap")
        vx -= convolve(vx, DIF_KERNEL[:, None], mode="wrap")

        # Advect
        ########
        advection = self.indices - velocity

        map_coordinates(advection, vy, output=vy, mode="wrap")
        map_coordinates(advection, vx, output=vx, mode="wrap")

        map_coordinates(advection, dye[0], output=dye[0], mode="wrap")
        map_coordinates(advection, dye[1], output=dye[1], mode="wrap")
        map_coordinates(advection, dye[2], output=dye[2], mode="wrap")

        # Reduce checkboard divergence
        gaussian_filter(velocity, 1, output=velocity)
        gaussian_filter(dye, 1, output=dye)

        super().render(canvas_view, colors_view, rect)
