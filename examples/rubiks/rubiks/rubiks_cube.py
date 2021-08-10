from itertools import product

import numpy as np
import cv2

from nurses_2.widgets import Widget

from .camera import Camera
from .cube import Cube


class RubiksCube(Widget):
    """
    A 3-dimensional Rubik's Cube.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.camera = Camera()
        self.cubes = [Cube(np.array(position)) for position in product((-1, 0, 1), repeat=3)]
        self._colors_buffer = np.zeros((2 * self.height, self.width, 3), dtype=np.uint8)

    def resize(self, dim):
        super().resize(dim)
        self._colors_buffer = np.zeros((2 * self.height, self.width, 3), dtype=np.uint8)
