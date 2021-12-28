from typing import NamedTuple

from math import e

__all__ = (
    "Color",
    "AColor",
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
        hexcode = hexcode.removeprefix("#")

        if len(hexcode) != 6:
            raise ValueError(f"{hexcode} has bad length")

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:], 16),
        )


class AColor(NamedTuple):
    """
    A tuple representing a color with an alpha channel.
    """
    red:   int
    green: int
    blue:  int
    alpha: int = 255

    @classmethod
    def from_hex(cls, hexcode: str):
        hexcode = hexcode.removeprefix("#")

        if len(hexcode) not in (6, 8):
            raise ValueError(f"{hexcode} has bad length")

        if len(hexcode) == 6:
            return cls(
                int(hexcode[:2], 16),
                int(hexcode[2:4], 16),
                int(hexcode[4:], 16),
            )

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:6], 16),
            int(hexcode[6:], 16)
        )

    def fog(self, distance):
        """
        Return color as if seen through a fog from a distance.

        Color will be multiplied by:
            `e ** -distance`
        """
        p = e ** -distance

        r, g, b, _ = self

        return type(self)(p * r, p * g, p * b)


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
    def from_colors(cls, fg_color: Color | AColor, bg_color: Color | AColor):
        """
        Return a `ColorPair` from two `Color`s.
        """
        return cls(*fg_color[:3], *bg_color[:3])

    @property
    def fg_color(self):
        return Color(*self[:3])

    @property
    def bg_color(self):
        return Color(*self[3:])


color_pair = ColorPair.from_colors  # Alias
