from functools import partial

import numpy as np

from .grid import Grid

from .colors import *

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
        ZERO,  # This color shouldn't be indexed, but little harm in including it.
    )[n]


class Count(Grid):
    def __init__(self, count, **kwargs):
        super().__init__(size=count.shape, is_light=True, default_color_pair=HIDDEN, **kwargs)

        self.canvas[1::2, 2::4] = stringify(count)
        self.colors[1::2, 2::4, :3] = np.dstack(colorify(count))
