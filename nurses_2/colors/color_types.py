from typing import NamedTuple

__all__ = (
    "RGB",
    "ColorPair",
)


class RGB(NamedTuple):
    """
    A tuple representing a 24-bit color.
    """
    r: int
    g: int
    b: int


class ColorPair(NamedTuple):
    """
    A tuple representing a foreground and background color.
    """
    fg_r: int  # foreground red
    fg_g: int  # foreground green
    fg_b: int  # foreground blue
    bg_r: int  # background red
    bg_g: int  # background green
    bg_b: int  # background blue
