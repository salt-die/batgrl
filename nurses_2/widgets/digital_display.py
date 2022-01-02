import numpy as np

from nurses_2.colors import Color, ColorPair, BLACK
from nurses_2.data_structures import Size
from nurses_2.widgets.text_widget import TextWidget

DIM_GREEN = Color.from_hex("062b0f")
BRIGHT_GREEN = Color.from_hex("33e860")

DIM_GREEN_ON_BLACK = ColorPair.from_colors(DIM_GREEN, BLACK)
BRIGHT_GREEN_ON_BLACK = ColorPair.from_colors(BRIGHT_GREEN, BLACK)

_SEGMENTS = {
 "a": np.s_[ 0, 1: -1],
 "b": np.s_[ 1: 3,  0],
 "c": np.s_[ 1: 3, -1],
 "d": np.s_[ 3, 1: -1],
 "e": np.s_[ 4: 6,  0],
 "f": np.s_[ 4: 6, -1],
 "g": np.s_[-1, 1: -1],
}

_DIGIT_TO_SEGMENTS = [
    "abcefg",
    "cf",
    "acdeg",
    "acdfg",
    "bcdf",
    "abdfg",
    "abdefg",
    "acf",
    "abcdefg",
    "abcdfg",
]


class DigitalDisplay(TextWidget):
    """
    A 7x6 seven-segment display widget.

    Use `show_digit` method display a specific digit or light/dim
    individual segments by setting a-g to True or False, e.g.,
    `digital_display.f = True`. The segments are labeled according
    to the following diagram:

    ```
        a
      ━━━━
    b┃    ┃c
     ┃  d ┃
      ━━━━
    e┃    ┃f
     ┃    ┃
      ━━━━
        g
    ```
    """
    def __init__(
        self,
        *,
        off_color_pair=DIM_GREEN_ON_BLACK,
        on_color_pair=BRIGHT_GREEN_ON_BLACK,
        **kwargs,
    ):
        kwargs.pop("size", None)
        kwargs.pop("size_hint", None)

        super().__init__(size=Size(7, 6), **kwargs)

        self.colors[:] = self.off_color_pair = off_color_pair
        self.on_color_pair = on_color_pair

        canvas = self.canvas
        canvas[[0, 3, 6], 1: -1] = "━"
        canvas[1: 3,  [0, -1]] = canvas[4: 6, [0, -1]] = "┃"

    def resize(self, size: Size):
        pass

    def show_digit(self, n):
        if n not in range(10):
            raise ValueError("n must one of (0, 1, 2, 3, 4, 5, 6, 7, 8, 9)")

        self.colors[:] = self.off_color_pair

        for segment in _DIGIT_TO_SEGMENTS[n]:
            setattr(self, segment, True)

    def __setattr__(self, attr, value):
        if attr in _SEGMENTS:
            self.colors[_SEGMENTS[attr]] = self.on_color_pair if value else self.off_color_pair
        else:
            super().__setattr__(attr, value)
