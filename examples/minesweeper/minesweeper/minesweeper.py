import numpy as np
from scipy.ndimage import convolve

from nurses_2.widgets import Widget
from nurses_2.widgets.widget_data_structures import Point

from .colors import HIDDEN
from .count import Count

SIZE = 16, 30
NMINES = 99
KERNEL = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]])
RNG = np.random.default_rng()


class MineSweeper(Widget):
    def __init__(self, pos=Point(0, 0), **kwargs):
        h, w = SIZE

        super().__init__(pos=pos, size=(2 * h + 1, 4 * w + 1), **kwargs)

        self.reset()

    def reset(self):
        self.children.clear()

        self.init_minefield()

        count = np.where(
            self.minefield == 1,
            0,
            convolve(self.minefield, KERNEL, mode='constant')
        )
        self.add_widget(Count(count))

    def init_minefield(self):
        self.minefield = minefield = np.zeros(SIZE, dtype=int)
        h, w = SIZE

        for _ in range(NMINES):
            while True:
                location =RNG.integers(h), RNG.integers(w)
                if minefield[location] == 0:
                    minefield[location] = 1
                    break

    def reveal(self, location):
        """
        Reveal `location` on the minefield.  Ends the game if there is a mine at `location`.
        Recurses over `location`'s neighbors if `location` has no neighboring mines.
        """
        self.revealed[location] = True

        if self.minefield[location]:
            return True

        elif self.count[location] == 0:
            for adjacent in product((-1, 0, 1), repeat=2):
                neighbor = tuple(np.array(location) + adjacent)
                if self.is_inbounds(neighbor) and not self.revealed[neighbor]:
                    self.reveal(neighbor)

    def is_inbounds(self, location):
        y, x = location
        return 0 <= y < self.height and 0 <= x < self.width
