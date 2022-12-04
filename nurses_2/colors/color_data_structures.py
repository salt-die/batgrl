"""
Color data structures.
"""
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

    Parameters
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.

    Attributes
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.

    Methods
    -------
    from_hex:
        Create a :class:`Color` from a hex code.
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    red:   int
    green: int
    blue:  int

    @classmethod
    def from_hex(cls, hexcode: str):
        """
        Create a :class:`Color` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.
        """
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

    Parameters
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.
    alpha : int
        The alpha component.

    Attributes
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.
    alpha : int
        The alpha component.

    Methods
    -------
    from_hex:
        Create an :class:`AColor` from a hex code.
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    red:   int
    green: int
    blue:  int
    alpha: int = 255

    @classmethod
    def from_hex(cls, hexcode: str):
        """
        Create an :class:`AColor` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.
        """
        hexcode = hexcode.removeprefix("#")

        if len(hexcode) not in (6, 8):
            raise ValueError(f"{hexcode} has bad length")

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:6], 16),
            int(hexcode[6:] or "ff", 16)
        )


class ColorPair(NamedTuple):
    """
    A foreground and background pair of 24-bit colors.

    Parameters
    ----------
    fg_red : int
        Foreground red component.
    fg_green : int
        Foreground green component.
    fg_blue : int
        Foreground blue component.
    bg_red : int
        Background red component.
    bg_green : int
        Background green component.
    bg_blue : int
        Background blue component.

    Attributes
    ----------
    fg_color : Color
        The foreground color.
    bg_color : Color
        The background color.
    fg_red : int
        Foreground red component.
    fg_green : int
        Foreground green component.
    fg_blue : int
        Foreground blue component.
    bg_red : int
        Background red component.
    bg_green : int
        Background green component.
    bg_blue : int
        Background blue component.

    Methods
    -------
    from_colors:
        Create a :class:`ColorPair` from two colors.
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    reversed:
        Return a :class:`ColorPair` with the foreground and background reversed.
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
        Create a :class:`ColorPair` from two colors.

        Parameters
        ----------
        fg_color : Color | AColor
            Foreground color.
        bg_color : Color | AColor
            Background color.
        """
        return cls(*fg_color[:3], *bg_color[:3])

    @property
    def fg_color(self) -> Color:
        """
        The foreground color.
        """
        return Color(*self[:3])

    @property
    def bg_color(self) -> Color:
        """
        The background color.
        """
        return Color(*self[3:])

    def reversed(self) -> "ColorPair":
        """
        Return a :class:`ColorPair` with the foreground and background reversed.
        """
        return ColorPair.from_colors(self.bg_color, self.fg_color)


class ColorTheme(NamedTuple):
    """
    A palette of colors used to paint an app's themable widgets.

    Parameters
    ----------
    primary_fg : Color
        Primary foreground color.
    primary_bg : Color
        Primary background color.
    primary_fg_light : Color
        Primary light foreground color.
    primary_bg_light : Color
        Primary light background color.
    primary_fg_dark : Color
        Primary dark foreground color.
    primary_bg_dark : Color
        Primary dark background color.
    secondary_fg : Color
        Secondary foreground color.
    secondary_bg : Color
        Secondary background color.
    primary_color_pair : ColorPair
        Primary color pair.
    primary_light_color_pair :  ColorPair
        Primary light color pair.
    primary_dark_color_pair : ColorPair
        Primary dark color pair.
    secondary_color_pair : ColorPair
        Secondary color pair.

    Attributes
    ----------
    primary_fg : Color
        Primary foreground color.
    primary_bg : Color
        Primary background color.
    primary_fg_light : Color
        Primary light foreground color.
    primary_bg_light : Color
        Primary light background color.
    primary_fg_dark : Color
        Primary dark foreground color.
    primary_bg_dark : Color
        Primary dark background color.
    secondary_fg : Color
        Secondary foreground color.
    secondary_bg : Color
        Secondary background color.
    primary_color_pair : ColorPair
        Primary color pair.
    primary_light_color_pair :  ColorPair
        Primary light color pair.
    primary_dark_color_pair : ColorPair
        Primary dark color pair.
    secondary_color_pair : ColorPair
        Secondary color pair.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    primary_fg: Color
    primary_bg: Color

    primary_fg_light: Color
    primary_bg_light: Color

    primary_fg_dark: Color
    primary_bg_dark: Color

    secondary_fg: Color
    secondary_bg: Color

    @property
    def primary_color_pair(self):
        """
        Primary color pair.
        """
        return ColorPair.from_colors(self.primary_fg, self.primary_bg)

    @property
    def primary_light_color_pair(self):
        """
        Primary light color pair.
        """
        return ColorPair.from_colors(self.primary_fg_light, self.primary_bg_light)

    @property
    def primary_dark_color_pair(self):
        """
        Primary dark color pair.
        """
        return ColorPair.from_colors(self.primary_fg_dark, self.primary_bg_dark)

    @property
    def secondary_color_pair(self):
        """
        Secondary color pair.
        """
        return ColorPair.from_colors(self.secondary_fg, self.secondary_bg)
