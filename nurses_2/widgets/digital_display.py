import numpy as np

from ..colors import Color, ColorPair, BLACK
from .text_widget import TextWidget, Size

DIM_GREEN = Color.from_hex("062b0f")
BRIGHT_GREEN = Color.from_hex("33e860")

DIM_GREEN_ON_BLACK = ColorPair.from_colors(DIM_GREEN, BLACK)
BRIGHT_GREEN_ON_BLACK = ColorPair.from_colors(BRIGHT_GREEN, BLACK)

_CHAR_TO_SEGMENTS = {
    " ": (),
    "0": ("a", "b", "c", "d", "e", "f"),
    "1": ("b", "c"),
    "2": ("a", "b", "g2", "g1", "e", "d"),
    "3": ("a", "b", "g2", "c", "d"),
    "4": ("f", "b", "g1", "g2", "c"),
    "5": ("a", "f", "g1", "m", "d"),
    "6": ("a", "f", "g1", "g2", "e", "c", "d"),
    "7": ("a", "b", "c"),
    "8": ("a", "f", "b", "g1", "g2", "e", "c", "d"),
    "9": ("a", "f", "b", "g1", "g2", "c", "d"),
    "a": ("e", "g1", "l", "d"),
    "b": ("f", "g1", "e", "m", "d"),
    "c": ("g1", "g2", "e", "d"),
    "d": ("k", "g2", "b", "c", "d"),
    "e": ("g1", "e", "k", "d"),
    "f": ("g1", "j", "g2", "l"),
    "g": ("j", "b", "g2", "c", "d"),
    "h": ("f", "g1", "e", "l"),
    "i": ("l",),
    "j": ("e", "k", "i"),
    "k": ("i", "l", "j", "m"),
    "l": ("f", "e"),
    "m": ("e", "g1", "l", "g2", "c"),
    "n": ("e", "g1", "l"),
    "o": ("g1", "g2", "e", "c", "d"),
    "p": ("f", "h", "g1", "e"),
    "q": ("j", "b", "g2", "c"),
    "r": ("e", "g1"),
    "s": ("g2", "m", "d"),
    "t": ("f", "g1", "e", "d"),
    "u": ("e", "d", "c"),
    "v": ("e", "k"),
    "w": ("e", "k", "m", "c"),
    "x": ("h", "j", "k", "m"),
    "y": ("i", "g2", "b", "c", "d"),
    "z": ("g1", "k", "d"),
    "A": ("a", "f", "b", "g1", "g2", "e", "c"),
    "B": ("a", "i", "b", "g2", "l", "c", "d"),
    "C": ("a", "f", "e", "d"),
    "D": ("a", "i", "b", "l", "c", "d"),
    "E": ("a", "f", "g1", "e", "d"),
    "F": ("a", "f", "g1", "e"),
    "G": ("a", "f", "g2", "e", "c", "d"),
    "H": ("f", "b", "g1", "g2", "e", "c"),
    "I": ("a", "i", "l", "d"),
    "J": ("e", "d", "c", "b"),
    "K": ("f", "g1", "j", "e", "m"),
    "L": ("f", "e", "d"),
    "M": ("f", "h", "j", "b", "e", "c"),
    "N": ("f", "h", "b", "e", "m", "c"),
    "O": ("a", "f", "b", "e", "c", "d"),
    "P": ("a", "f", "b", "g1", "g2", "e"),
    "Q": ("a", "f", "b", "e", "m", "c", "d"),
    "R": ("a", "f", "b", "g1", "g2", "e", "m"),
    "S": ("a", "f", "g1", "g2", "c", "d"),
    "T": ("a", "i", "l"),
    "U": ("f", "b", "e", "c", "d"),
    "V": ("f", "e", "k", "j"),
    "W": ("f", "b", "e", "k", "m", "c"),
    "X": ("h", "j", "k", "m"),
    "Y": ("f", "b", "g1", "g2", "c", "d"),
    "Z": ("a", "j", "k", "d"),
    "!": ("b", "c", "dp"),
    '"': ("i", "b"),
    "#": ("g1", "i", "g2", "b", "l", "c", "d"),
    "$": ("a", "f", "i", "g1", "g2", "l", "c", "d"),
    "%": ("f", "h", "j", "g1", "g2", "k", "m", "c"),
    "&": ("a", "h", "i", "g1", "e", "m", "d", "c"),
    "'": ("i",),
    "(": ("j", "m"),
    ")": ("h", "k"),
    "*": ("h", "i", "j", "g1", "g2", "k", "l", "m"),
    "+": ("i", "g1", "g2", "l"),
    ",": ("k",),
    "-": ("g1", "g2"),
    ".": ("dp",),
    "/": ("k", "j"),
    ":": ("i", "l"),
    ";": ("i", "k"),
    "<": ("g1", "j", "m"),
    "=": ("g1", "g2", "d"),
    ">": ("h", "k", "g2"),
    "?": ("a", "b", "g2", "l", "dp"),
    "@": ("i", "g2", "b", "a", "f", "e", "d"),
    "[": ("a", "f", "e", "d"),
    "\\": ("h", "m"),
    "]": ("a", "b", "c", "d"),
    "^": ("k", "m"),
    "_": ("d",),
    "`": ("h",),
    "{": ("a", "h", "g1", "k", "d"),
    "|": ("i", "l"),
    "}": ("a", "j", "g2", "m", "d"),
    "~": ("g1", "j", "g2", "k"),
}


class Segment:
    def __init__(self, slice_):
        self.slice = slice_

    def __get__(self, owner, instance):
        return (instance.colors[self.slice] == instance.on_color_pair).all()

    def __set__(self, instance, value):
        instance.colors[self.slice] = instance.on_color_pair if value else instance.off_color_pair


class DigitalDisplay(TextWidget):
    r"""
    A 7x8 14-segment (plus decimal point) display widget.

    Parameters
    ----------
    off_color_pair : ColorPair, default: DIM_GREEN_ON_BLACK
        Color pair of off segments.
    on_color_pair : ColorPair, default: BRIGHT_GREEN_ON_BLACK
        Color pair of on segments.

    Use `show_char` method to display an ascii character or turn on/off
    individual segments by setting one of ("a", "b", "c", "d", "e",
    "f", "g1", "g2", "h", "i", "j", "k", "l", "m", "dp") to True or False.
    E.g., `digital_display.f = True`. The segments are labeled according
    to the following diagram:

    ```
        a
      ━━━━━
    f┃  ┃i ┃b     h \   / j
     ┃  ┃  ┃         \ /
                 g1 ━━ ━━ g2
    e┃  ┃l ┃c        / \
     ┃  ┃  ┃      k /   \ m
      ━━━━━ ● dp
        d
    ```
    """
    a  = Segment(np.s_[0, 1: 6])
    b  = Segment(np.s_[1: 3, 6])
    c  = Segment(np.s_[4: 6, 6])
    d  = Segment(np.s_[6, 1: 6])
    e  = Segment(np.s_[4: 6,  0])
    f  = Segment(np.s_[1: 3,  0])
    g1 = Segment(np.s_[3, 1: 3])
    g2 = Segment(np.s_[3, 4: 6])
    h  = Segment(((1, 2), (1, 2)))
    i  = Segment(np.s_[1: 3, 3])
    j  = Segment(((1, 2), (5, 4)))
    k  = Segment(((4, 5), (2, 1)))
    l  = Segment(np.s_[4: 6, 3])
    m  = Segment(((4, 5), (4, 5)))
    dp = Segment(np.s_[6, 7:8])

    def __init__(
        self,
        *,
        off_color_pair: ColorPair=DIM_GREEN_ON_BLACK,
        on_color_pair: ColorPair=BRIGHT_GREEN_ON_BLACK,
        **kwargs,
    ):
        kwargs.pop("size", None)
        kwargs.pop("size_hint", None)

        super().__init__(size=Size(7, 8), **kwargs)

        self.off_color_pair = off_color_pair
        self.on_color_pair = on_color_pair

        canvas = self.canvas
        canvas[[0, 6], 1: 6] = canvas[3, 1: 3] = canvas[3, 4: 6] = "━"
        canvas[1: 3,  [0, 3, 6]] = canvas[4: 6, [0, 3, 6]] = "┃"
        canvas[(1, 2, 4, 5), (1, 2, 4, 5)] = "\\"
        canvas[(1, 2, 4, 5), (5, 4, 2, 1)] = "/"
        canvas[6, 7] = "●"

        self._where_segments = canvas != self.default_char
        self.colors[self._where_segments] = off_color_pair

    def resize(self, size: Size):
        pass

    def show_char(self, char: str):
        if char not in _CHAR_TO_SEGMENTS:
            raise ValueError(f"{char} is not an ascii character")

        self.colors[self._where_segments] = self.off_color_pair

        for segment in _CHAR_TO_SEGMENTS[char]:
            setattr(self, segment, True)
