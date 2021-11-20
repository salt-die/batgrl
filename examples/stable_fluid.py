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
        self.curl_mask = np.triu(np.ones((2, 2), dtype=bool), k=1)

    def render(self, canvas_view, colors_view, rect: Rect):
        h, w = self.texture.shape
        vy, vx = velocity = self.velocity
        dye = self.dye
        curl_mask = self.curl_mask

        advection = self.indices - velocity

        map_coordinates(advection, vy, output=vy, mode="wrap")
        map_coordinates(advection, vx, output=vx, mode="wrap")
        map_coordinates(advection, dye, output=dye, mode="wrap")

        # Reduce checkboard divergence
        gaussian_filter(velocity, 1, output=velocity)
        gaussian_filter(dye, 1, output=dye)

        jacobian = np.stack((np.gradient(vy), np.gradient(vx))).reshape(2, 2, h, w)

        divergence = jacobian.trace()
        curl = (jacobian[curl_mask] - jacobian[curl_mask.T]).squeeze()

        super().render(canvas_view, colors_view, rect)
