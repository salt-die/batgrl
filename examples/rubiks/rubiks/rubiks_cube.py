from itertools import product

import numpy as np
import cv2

from nurses_2.widgets import Widget
from nurses_2.colors import RED, YELLOW, WHITE, GREEN, BLUE, Color

from .camera import Camera
from .cube import Cube

FRONT_COLOR  = RED
BACK_COLOR   = ORANGE = from_hex("f46e07")
LEFT_COLOR   = YELLOW
RIGHT_COLOR  = WHITE
TOP_COLOR    = GREEN
BOTTOM_COLOR = BLUE


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

    def render_cube(self, cube):
        """
        Render a cube to the _colors_buffer.
        """