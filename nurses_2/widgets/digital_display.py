import numpy as np

from nurses_2.colors import Color, ColorPair, BLACK
from nurses_2.data_structures import Size
from nurses_2.widgets.text_widget import TextWidget

DIM_GREEN = Color.from_hex("062b0f")
BRIGHT_GREEN = Color.from_hex("33e860")

DIM_GREEN_ON_BLACK = ColorPair.from_colors(DIM_GREEN, BLACK)
BRIGHT_GREEN_ON_BLACK = ColorPair.from_colors(BRIGHT_GREEN, BLACK)

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


class Segment:
    def __init__(self, slice_):
        self.slice = slice_

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, owner, instance):
        return (instance.colors[self.slice] == instance.on_color_pair).all()

    def __set__(self, instance, value):
        instance.colors[self.slice] = instance.on_color_pair if value else instance.off_color_pair


class DigitalDisplay(TextWidget):
    """
    A 7x6 seven-segment display widget.

    Parameters
    ----------
    off_color_pair : ColorPair, default: DIM_GREEN_ON_BLACK
        Color pair of off segments.
    on_color_pair : ColorPair, default: BRIGHT_GREEN_ON_BLACK
        Color pair of on segments.

    Use `show_digit` method to display a specific digit or light/dim
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
    a = Segment(np.s_[ 0, 1: -1])
    b = Segment(np.s_[ 1: 3,  0])
    c = Segment(np.s_[ 1: 3, -1])
    d = Segment(np.s_[ 3, 1: -1])
    e = Segment(np.s_[ 4: 6,  0])
    f = Segment(np.s_[ 4: 6, -1])
    g = Segment(np.s_[-1, 1: -1])

    def __init__(
        self,
        *,
        off_color_pair: ColorPair=DIM_GREEN_ON_BLACK,
        on_color_pair: ColorPair=BRIGHT_GREEN_ON_BLACK,
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

    def show_digit(self, digit: int):
        if digit not in range(10):
            raise ValueError(f"not a digit")

        self.colors[:] = self.off_color_pair

        for segment in _DIGIT_TO_SEGMENTS[digit]:
            setattr(self, segment, True)
