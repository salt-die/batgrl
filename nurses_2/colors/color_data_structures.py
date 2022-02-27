from math import e
from typing import NamedTuple

__all__ = (
    "Color",
    "AColor",
    "ColorPair",
    "ColorTheme",
)


class Color(NamedTuple):
    """
    A 24-bit color.
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
    A 24-bit color with an alpha channel.
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

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:6], 16),
            int(hexcode[6:] or "ff", 16)
        )

    def fog(self, distance):
        """
        Return color as if seen through a fog from a distance.

        Non-alpha channels will be multiplied by:
            `e ** -distance`
        """
        p = e ** -distance

        r, g, b, a = self

        return type(self)(int(p * r), int(p * g), int(p * b), a)


class ColorPair(NamedTuple):
    """
    A foreground and background pair of 24-bit colors.
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


class ColorTheme(NamedTuple):
    """
    A palette of colors used to paint an app's themable widgets.
    """
    primary_foreground: Color
    primary_background: Color

    highlighted_foreground: Color
    highlighted_background: Color

    accented_foreground: Color
    accented_background: Color

    @property
    def primary_color_pair(self):
        return ColorPair.from_colors(self.primary_foreground, self.primary_background)

    @property
    def highlighted_color_pair(self):
        return ColorPair.from_colors(self.highlighted_foreground, self.highlighted_background)

    @property
    def accented_color_pair(self):
        return ColorPair.from_colors(self.accented_foreground, self.accented_background)
