from typing import NamedTuple

from ..utils import clamp

__all__ = (
    "Color",
    "ColorPair",
    "color_pair",
)


class Color(NamedTuple):
    """
    A tuple representing a 24-bit color.
    """
    red:   int
    green: int
    blue:  int

    @classmethod
    def from_hex(cls, hexcode: str):
        if hexcode.startswith("#"):
            hexcode = hexcode[1:]

        assert len(hexcode) == 6, f'{hexcode} has bad length'

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:], 16),
        )

    def fog(self, distance, scale=7, exp=.1):
        """
        Return color as if seen through a fog from a distance.

        Color will be multiplied by:
            `scale ** (-distance * exp)`
        """
        factor = scale ** (-distance * exp)

        return type(self)(
            *(clamp(channel * factor, 0, 255) for channel in self)
        )


class ColorPair(NamedTuple):
    """
    A tuple representing a foreground and background color.
    """
    fg_red:   int
    fg_green: int
    fg_blue:  int
    bg_red:   int
    bg_green: int
    bg_blue:  int

    @classmethod
    def from_colors(cls, fg_color: Color, bg_color: Color):
        """
        Return a `ColorPair` from two `Color`s.
        """
        return cls(*fg_color, *bg_color)

    @property
    def fg_color(self):
        return Color(*self[:3])

    @property
    def bg_color(self):
        return Color(*self[3:])


color_pair = ColorPair.from_colors  # Alias
