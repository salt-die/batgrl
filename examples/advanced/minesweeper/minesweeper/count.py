from functools import partial

import numpy as np

from .colors import *
from .grid import Grid
from .unicode_chars import BOMB


@np.vectorize
def stringify(n):
    return " " if n == 0 else str(n)

@partial(np.vectorize, otypes=[np.uint8, np.uint8, np.uint8])
def colorify(n):
    return (
        ZERO,
        ONE,
        TWO,
        THREE,
        FOUR,
        FIVE,
        SIX,
        SEVEN,
        EIGHT,
        ZERO,
    )[n]


class Count(Grid):
    """
    A widget that displays the number of adjacent bombs of each cell. This widget will be
    initially hidden by the `MineField` widget.
    """
    def __init__(self, count, minefield, **kwargs):
        super().__init__(
            size=count.shape,
            is_light=True,
            default_color_pair=COUNT,
            **kwargs,
        )
        v_center, h_center = self.cell_center_indices

        self.canvas[v_center, h_center] = stringify(count)
        self.canvas[v_center, h_center][minefield == 1] = BOMB
        self.normalize_canvas()  # Null characters are inserted after the full-width `BOMB`s.

        self.colors[v_center, h_center, :3] = np.dstack(colorify(count))
