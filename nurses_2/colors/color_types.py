from typing import NamedTuple

__all__ = (
    "RGB",
    "ColorPair",
)


class RGB(NamedTuple):
    """
    A tuple representing a 24-bit color.
    """
    red:   int
    green: int
    blue:  int


class ColorPair(NamedTuple):
    """
    A tuple representing a foreground and background color.
    """
    foreground_red:   int
    foreground_green: int
    foreground_blue:  int
    background_red:   int
    background_green: int
    background_blue:  int
