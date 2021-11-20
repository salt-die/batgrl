"""
Stable fluid simulation. WIP
"""
import numpy as np

from scipy.ndimage import map_coordinates, gaussian_filter

from nurses_2.widgets.graphic_widget import GraphicWidget


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

    def render(self, canvas_view, colors_view, rect: Rect):
        velocity = self.velocity
        dye = self.dye

        advection = self.indices - velocity

        map_coordinates(advection, velocity[0], output=velocity[0], mode="wrap")
        map_coordinates(advection, velocity[1], output=velocity[1], mode="wrap")
        map_coordinates(advection, dye, output=dye, mode="wrap")

        super().render(canvas_view, colors_view, rect)
