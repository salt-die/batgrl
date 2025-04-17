from functools import partial

import numpy as np

from .colors import (
    BORDER,
    COUNT_SQUARE,
    EIGHT,
    FIVE,
    FOUR,
    ONE,
    SEVEN,
    SIX,
    THREE,
    TWO,
    ZERO,
)
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
    A gadget that displays the number of adjacent bombs of each cell. This gadget will
    be initially hidden by the `MineField` gadget.
    """

    def __init__(self, count, minefield, **kwargs):
        super().__init__(size=count.shape, is_light=True, **kwargs)
        v_center, h_center = self.cell_center_indices

        self.canvas["fg_color"] = BORDER
        self.canvas["bg_color"] = COUNT_SQUARE
        self.chars[v_center, h_center] = stringify(count)
        self.chars[v_center, h_center][minefield == 1] = BOMB
        self.canvas["fg_color"][v_center, h_center] = np.dstack(colorify(count))

        ys, xs = (self.chars == BOMB).nonzero()
        self.chars[ys, xs + 1] = ""
