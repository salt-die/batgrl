from typing import NamedTuple

__all__ = (
    "Color",
    "ColorPair",
    "color_pair"
)

def clamp_channel(channel):
    if channel < 0:
        return 0
    if channel > 255:
        return 255
    return channel


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
            *(clamp_channel(channel * factor) for channel in self)
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

    @classmethod
    def from_colors(cls, foreground_color: Color, background_color: Color):
        """
        Return a `ColorPair` from two `Color`s.
        """
        return cls(*foreground_color, *background_color)


color_pair = ColorPair.from_colors  # Alias
