"""
Stable fluid simulation. WIP
"""
import numpy as np

from scipy.ndimage import map_coordinates, gaussian_filter
from scipy.ndimage.filters import convolve

from nurses_2.widgets.graphic_widget import GraphicWidget

DIF_KERNEL = np.array([-.5, 0, .5])

# Steps to solve:
# * Advect velocity
# * Vorticity
# * Vorticity Confinement

class StableFluid(GraphicWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(self.size)

    def resize(self, size: Size):
        super().resize(size)

        h, w = self.texture.shape

        self.dye = np.zeros((h, w))
        self.indices = np.indices((h, w))
        self.velocity = np.zeros((2, h, w))

    def _init_inflow(self):
        """
        Init constant velocity field.
        """

    def render(self, canvas_view, colors_view, rect: Rect):
        vy, vx = velocity = self.velocity
        dye = self.dye

        # Advect
        ########
        advection = self.indices - velocity

        map_coordinates(advection, vy, output=vy, mode="wrap")
        map_coordinates(advection, vx, output=vx, mode="wrap")
        map_coordinates(advection, dye, output=dye, mode="wrap")

        # Reduce checkboard divergence
        gaussian_filter(velocity, 1, output=velocity)
        gaussian_filter(dye, 1, output=dye)

        # Divergence
        ############
        div_y = convolve(vy, DIF_KERNEL[None], mode="wrap")
        div_x = convolve(vx, DIF_KERNEL[:, None], mode="wrap")

        div = div_y + div_x

        # Project
        #########
        vy -= div_y
        vx -= div_x

        super().render(canvas_view, colors_view, rect)
