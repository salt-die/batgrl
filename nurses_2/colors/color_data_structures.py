from typing import NamedTuple

__all__ = (
    "Color",
    "ColorPair",
)


class Color(NamedTuple):
    """
    A tuple representing a 24-bit color.
    """
    red:   int
    green: int
    blue:  int

    @classmethod
    def from_hex(cls, hexcode):
        hexcode = hexcode.removeprefix("#")

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:], 16)
        )


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
