import numpy as np
from scipy.ndimage import convolve

from nurses_2.widgets import Widget
from nurses_2.widgets.widget_data_structures import Point

from .colors import HIDDEN
from .count import Count
from .grid import Grid
from .hidden import Hidden

SIZE = 16, 30
NMINES = 99
KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
RNG = np.random.default_rng()
V_SPACING = Grid.V_SPACING
H_SPACING = Grid.H_SPACING


class MineSweeper(Widget):
    def __init__(self, pos=Point(0, 0), **kwargs):
        h, w = SIZE

        super().__init__(pos=pos, size=(V_SPACING * h + 1, H_SPACING * w + 1), **kwargs)

        self.reset()

    def reset(self):
        self.children.clear()

        minefield = self.create_minefield()
        count = convolve(minefield, KERNEL, mode='constant')
        self.add_widgets(Count(count), Hidden(count, minefield))

    def create_minefield(self):
        minefield = np.zeros(SIZE, dtype=int)
        h, w = SIZE

        for _ in range(NMINES):
            while True:
                location =RNG.integers(h), RNG.integers(w)
                if minefield[location] == 0:
                    minefield[location] = 1
                    break

        return minefield
