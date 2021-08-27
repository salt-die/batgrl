from functools import partial

import numpy as np

from .colors import *
from .grid import Grid

BOMB = "💣"

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
    def __init__(self, count, minefield, **kwargs):
        super().__init__(
            size=count.shape,
            is_light=True,
            default_color_pair=COUNT,
            **kwargs,
        )
        vs, hs = self.V_SPACING, self.H_SPACING

        self.canvas[vs//2::vs, hs//2::hs] = stringify(count)
        self.canvas[vs//2::vs, hs//2::hs][minefield == 1] = BOMB

        self.colors[vs//2::vs, hs//2::hs, :3] = np.dstack(colorify(count))
