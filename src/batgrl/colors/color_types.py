"""Color data structures."""

import re
from typing import NamedTuple, Self, TypedDict

__all__ = ["AColor", "Color", "ColorTheme"]


def validate_hexcode(hexcode: str) -> bool:
    return bool(re.match(r"^#?[0-9a-fA-F]{6}$", hexcode))


def validate_ahexcode(ahexcode: str) -> bool:
    return bool(re.match(r"^#?[0-9a-fA-F]{8}$", ahexcode))


def _to_hex(channel):
    return hex(channel)[2:].zfill(2)


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
    from_hex(hexcode)
        Create a :class:`Color` from a hex code.
    to_hex()
        Return color's hexcode.
    """

    red: int
    green: int
    blue: int

    @classmethod
    def from_hex(cls, hexcode: str) -> Self:
        """
        Create a :class:`Color` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.

        Returns
        -------
        Color
            A new color.
        """
        if not validate_hexcode(hexcode):
            raise ValueError(f"{hexcode!r} is not a valid hex code.")

        digits = hexcode.removeprefix("#")
        return cls(int(digits[:2], 16), int(digits[2:4], 16), int(digits[4:], 16))

    def to_hex(self) -> str:
        """
        Return color's hexcode.

        Returns
        -------
        str
            The hexcode of the color.
        """
        hexcode = "".join(_to_hex(channel) for channel in self)
        return f"#{hexcode}"


class AColor(NamedTuple):
    """
    A 32-bit color with an alpha channel.

    Parameters
    ----------
    red : int
        The red component.
    green : int
        The green component.
    blue : int
        The blue component.
    alpha : int, default: 255
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
    from_hex(hexcode)
        Create an :class:`AColor` from a hex code.
    to_hex()
        Return color's hexcode.
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    @classmethod
    def from_hex(cls, hexcode: str) -> Self:
        """
        Create an :class:`AColor` from a hex code.

        Parameters
        ----------
        hexcode : str
            A color hex code.

        Returns
        -------
        AColor
            A new color with alpha.
        """
        if not validate_ahexcode(hexcode) and not validate_hexcode(hexcode):
            raise ValueError(f"{hexcode!r} is not a valid hex code")

        digits = hexcode.removeprefix("#")
        return cls(
            int(digits[:2], 16),
            int(digits[2:4], 16),
            int(digits[4:6], 16),
            int(digits[6:] or "ff", 16),
        )

    def to_hex(self) -> str:
        """
        Return color's hexcode.

        Returns
        -------
        str
            The hexcode of the color.
        """
        hexcode = "".join(_to_hex(channel) for channel in self)
        return f"#{hexcode}"


class ColorPair(TypedDict):
    """
    A foreground and background hexcode.

    Attributes
    ----------
    fg : str
        The foreground hex code.
    bg : str
        The background hex code.
    """

    fg: str
    """The foreground hex code."""
    bg: str
    """The background hex code."""


class ColorTheme(TypedDict, total=False):
    """
    Colors for themable gadgets.

    Missing colors will use the default color theme.

    Attributes
    ----------
    primary : ColorPair
        The primary color pair.
    text_pad_line_highlight : ColorPair
        Text pad line highlight color pair.
    text_pad_selection_highlight : ColorPair
        Text pad selection color pair.
    textbox_primary : ColorPair
        Text pad primary color pair.
    textbox_selection_highlight : ColorPair
        Textbox selection color pair.
    textbox_placeholder : ColorPair
        Textbox placeholder color pair.
    button_normal : ColorPair
        Button normal color pair.
    button_hover : ColorPair
        Button hover color pair.
    button_press : ColorPair
        Button press color pair.
    button_disallowed : ColorPair
        Button disallowed color pair.
    menu_item_hover : ColorPair
        Menu item hover color pair.
    menu_item_selected : ColorPair
        Menu item selected color pair.
    menu_item_disallowed : ColorPair
        Menu item disallowed color pair.
    titlebar_normal : ColorPair
        Titlebar normal color pair.
    titlebar_inactive : ColorPair
        Titlebar inactive color pair.
    data_table_sort_indicator : ColorPair
        Data table sort indicator color pair.
    data_table_hover : ColorPair
        Data table hover color pair.
    data_table_stripe : ColorPair
        Data table stripe color pair.
    data_table_stripe_hover : ColorPair
        Data table stripe hover color pair.
    data_table_selected : ColorPair
        Data table selected color pair.
    data_table_selected_hover : ColorPair
        Data table selected hover color pair.
    progress_bar : ColorPair
        Progress bar color pair.
    markdown_link : ColorPair
        Markdown link color pair.
    markdown_link_hover : ColorPair
        Markdown link hover color pair.
    markdown_inline_code : ColorPair
        Markdown inline code color pair.
    markdown_quote : ColorPair
        Markdown quote color pair.
    markdown_title : ColorPair
        Markdown title color pair.
    markdown_image : ColorPair
        Markdown image color pair.
    markdown_block_code_background : str
        Markdown block code background color hexcode.
    markdown_quote_block_code_background : str
        Markdown quote block code background color hexcode.
    markdown_header_background : str
        Markdown header background color hexcode.
    scroll_view_scrollbar : str
        Scroll view scrollbar color hexcode.
    scroll_view_indicator_normal : str
        Scroll view indicator normal color hexcode.
    scroll_view_indicator_hover : str
        Scroll view indicator hover color hexcode.
    scroll_view_indicator_press : str
        Scroll view indicator press color hexcode.
    window_border_normal : str
        Window border normal color hexcode.
    window_border_inactive : str
        Window border inactive color hexcode.
    """

    primary: ColorPair
    """The primary color pair."""
    text_pad_line_highlight: ColorPair
    """Text pad line highlight color pair."""
    text_pad_selection_highlight: ColorPair
    """Text pad selection color pair."""
    textbox_primary: ColorPair
    """Text pad primary color pair."""
    textbox_selection_highlight: ColorPair
    """Textbox selection color pair."""
    textbox_placeholder: ColorPair
    """Textbox placeholder color pair."""
    button_normal: ColorPair
    """Button normal color pair."""
    button_hover: ColorPair
    """Button hover color pair."""
    button_press: ColorPair
    """Button press color pair."""
    button_disallowed: ColorPair
    """Button disallowed color pair."""
    menu_item_hover: ColorPair
    """Menu item hover color pair."""
    menu_item_selected: ColorPair
    """Menu item selected color pair."""
    menu_item_disallowed: ColorPair
    """Menu item disallowed color pair."""
    titlebar_normal: ColorPair
    """Titlebar normal color pair."""
    titlebar_inactive: ColorPair
    """Titlebar inactive color pair."""
    data_table_sort_indicator: ColorPair
    """Data table sort indicator color pair."""
    data_table_hover: ColorPair
    """Data table hover color pair."""
    data_table_stripe: ColorPair
    """Data table stripe color pair."""
    data_table_stripe_hover: ColorPair
    """Data table stripe hover color pair."""
    data_table_selected: ColorPair
    """Data table selected color pair."""
    data_table_selected_hover: ColorPair
    """Data table selected hover color pair."""
    progress_bar: ColorPair
    """Progress bar color pair."""
    markdown_link: ColorPair
    """Markdown link color pair."""
    markdown_link_hover: ColorPair
    """Markdown link hover color pair."""
    markdown_inline_code: ColorPair
    """Markdown inline code color pair."""
    markdown_quote: ColorPair
    """Markdown quote color pair."""
    markdown_title: ColorPair
    """Markdown title color pair."""
    markdown_image: ColorPair
    """Markdown image color pair."""
    markdown_block_code_background: str
    """Markdown block code background color hexcode."""
    markdown_quote_block_code_background: str
    """Markdown quote block code background color hexcode."""
    markdown_header_background: str
    """Markdown header background color hexcode."""
    scroll_view_scrollbar: str
    """Scroll view scrollbar color hexcode."""
    scroll_view_indicator_normal: str
    """Scroll view indicator normal color hexcode."""
    scroll_view_indicator_hover: str
    """Scroll view indicator hover color hexcode."""
    scroll_view_indicator_press: str
    """Scroll view indicator press color hexcode."""
    window_border_normal: str
    """Window border normal color hexcode."""
    window_border_inactive: str
    """Window border inactive color hexcode."""
