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
            raise ValueError(f"{hexcode!r} is not a valid hex code")

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
            raise ValueError(f"{hexcode!r} is not a valid hex code")

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

    @classmethod
    def from_hexes(cls, fg_hexcode: str, bg_hexcode: str):
        """
        Create a :class:`ColorPair` from two hex codes.

        Parameters
        ----------
        fg_hexcode : int | str
            Hex code for foreground color.
        bg_hexcode : int | str
            Hex code for background color.
        """
        return cls(*AColor.from_hex(fg_hexcode)[:3], *AColor.from_hex(bg_hexcode)[:3])

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
    Colors used on themable widgets.

    Parameters
    ----------
    primary : ColorPair
        Primary color pair.
    panel : ColorPair
        Text panel color pair.
    button_normal : ColorPair
        Button color pair.
    button_hover : ColorPair
        Hovored button color pair.
    button_press : ColorPair
        Pressed button color pair.
    item_hover : ColorPair
        Hovered item color pair.
    item_selected : ColorPair
        Selected item color pair.
    titlebar_normal : ColorPair
        Titlebar color pair.
    titlebar_inactive : ColorPair
        Inactive titlebar color pair.
    border_normal : AColor
        Border color.
    border_inactive : AColor
        Inactive border color.
    scrollbar : Color
        Scrollbar color.
    scrollbar_indicator_normal : Color
        Scrollbar indicator color.
    scrollbar_indicator_hover : Color
        Hovered scrollbar indicator color.
    scrollbar_indicator_press : Color
        Pressed scrollbar indicator color.

    Attributes
    ----------
    primary : ColorPair
        Primary color pair.
    panel : ColorPair
        Text panel color pair.
    button_normal : ColorPair
        Button color pair.
    button_hover : ColorPair
        Hovored button color pair.
    button_press : ColorPair
        Pressed button color pair.
    item_hover : ColorPair
        Hovered item color pair.
    item_selected : ColorPair
        Selected item color pair.
    titlebar_normal : ColorPair
        Titlebar color pair.
    titlebar_inactive : ColorPair
        Inactive titlebar color pair.
    border_normal : AColor
        Border color.
    border_inactive : AColor
        Inactive border color.
    scrollbar : Color
        Scrollbar color.
    scrollbar_indicator_normal : Color
        Scrollbar indicator color.
    scrollbar_indicator_hover : Color
        Hovered scrollbar indicator color.
    scrollbar_indicator_press : Color
        Pressed scrollbar indicator color.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    primary: ColorPair
    panel: ColorPair
    button_normal: ColorPair
    button_hover: ColorPair
    button_press: ColorPair
    item_hover: ColorPair
    item_selected: ColorPair
    item_disabled: ColorPair
    titlebar_normal: ColorPair
    titlebar_inactive: ColorPair
    border_normal: AColor
    border_inactive: AColor
    scrollbar: Color
    scrollbar_indicator_normal: Color
    scrollbar_indicator_hover: Color
    scrollbar_indicator_press: Color
