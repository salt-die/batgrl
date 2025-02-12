"""Color data structures."""

import re
from typing import Final, NamedTuple, Self, TypedDict

__all__ = ["AColor", "Color", "ColorTheme"]

_HEXCODE_RE: Final = re.compile(r"^#?[0-9a-fA-F]{6}$")
_AHEXCODE_RE: Final = re.compile(r"^#?[0-9a-fA-F]{8}$")

type Hexcode = str
"""
A hexcode string for 24-bit color. Six hex digits optionally preceded by "#", e.g.,
"#abc123".
"""

type AHexcode = str
"""
A hexcode string for a 32-bit color. Six or eight hex digits optionally preceded by
"#", e.g., "#abcd1234". If eight hex digits are given, the last two digits specify the
alpha channel, otherwise, the alpha channel value defaults to 255 so that the six digit
string ``"#abc123`` is equivalent to ``"#abc123ff"``.
"""


def validate_hexcode(hexcode: Hexcode) -> bool:
    return bool(_HEXCODE_RE.match(hexcode))


def validate_ahexcode(ahexcode: AHexcode) -> bool:
    return validate_hexcode(ahexcode) or bool(_AHEXCODE_RE.match(ahexcode))


def _to_hex(channel: int):
    return f"{channel:02x}"


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
    def from_hex(cls, hexcode: Hexcode) -> Self:
        """
        Create a :class:`Color` from a hex code.

        Parameters
        ----------
        hexcode : Hexcode
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

    def to_hex(self) -> Hexcode:
        """
        Return color's hexcode.

        Returns
        -------
        Hexcode
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
    def from_hex(cls, hexcode: AHexcode) -> Self:
        """
        Create an :class:`AColor` from a hex code.

        If the hexcode only has six hex digits, the alpha channel's value will default
        to 255.

        Parameters
        ----------
        hexcode : AHexcode
            A color hex code.

        Returns
        -------
        AColor
            A new color with an alpha channel.
        """
        if not validate_ahexcode(hexcode):
            raise ValueError(f"{hexcode!r} is not a valid hex code")

        digits = hexcode.removeprefix("#")
        return cls(
            int(digits[:2], 16),
            int(digits[2:4], 16),
            int(digits[4:6], 16),
            int(digits[6:] or "ff", 16),
        )

    def to_hex(self) -> AHexcode:
        """
        Return color's hexcode.

        Returns
        -------
        AHexcode
            The hexcode of the color.
        """
        hexcode = "".join(_to_hex(channel) for channel in self)
        return f"#{hexcode}"


class ColorTheme(TypedDict, total=False):
    """
    Colors for themable gadgets.

    Missing colors will use the default color theme.

    Attributes
    ----------
    primary_fg : Hexcode
        The primary foreground color.
    primary_bg : Hexcode
        The primary background color.
    text_pad_line_highlight_fg: Hexcode
        Text pad line highlight foreground color.
    text_pad_line_highlight_bg: Hexcode
        Text pad line highlight background color.
    text_pad_selection_highlight_fg : Hexcode
        Text pad selection foreground color.
    text_pad_selection_highlight_bg : Hexcode
        Text pad selection background color.
    textbox_primary_fg : Hexcode
        Text pad primary foreground color.
    textbox_primary_bg : Hexcode
        Text pad primary background color.
    textbox_selection_highlight_fg : Hexcode
        Textbox selection foreground color.
    textbox_selection_highlight_bg : Hexcode
        Textbox selection background color.
    textbox_placeholder_fg : Hexcode
        Textbox placeholder foreground color.
    textbox_placeholder_bg : Hexcode
        Textbox placeholder background color.
    button_normal_fg : Hexcode
        Button normal foreground color.
    button_normal_bg : Hexcode
        Button normal background color.
    button_hover_fg : Hexcode
        Button hover foreground color.
    button_hover_bg : Hexcode
        Button hover background color.
    button_press_fg : Hexcode
        Button press foreground color.
    button_press_bg : Hexcode
        Button press background color.
    button_disallowed_fg : Hexcode
        Button disallowed foreground color.
    button_disallowed_bg : Hexcode
        Button disallowed background color.
    menu_item_hover_fg : Hexcode
        Menu item hover foreground color.
    menu_item_hover_bg : Hexcode
        Menu item hover background color.
    menu_item_selected_fg : Hexcode
        Menu item selected foreground color.
    menu_item_selected_bg : Hexcode
        Menu item selected background color.
    menu_item_disallowed_fg : Hexcode
        Menu item disallowed foreground color.
    menu_item_disallowed_bg : Hexcode
        Menu item disallowed background color.
    titlebar_normal_fg : Hexcode
        Titlebar normal foreground color.
    titlebar_normal_bg : Hexcode
        Titlebar normal background color.
    titlebar_inactive_fg : Hexcode
        Titlebar inactive foreground color.
    titlebar_inactive_bg : Hexcode
        Titlebar inactive background color.
    data_table_sort_indicator_fg : Hexcode
        Data table sort indicator foreground color.
    data_table_sort_indicator_bg : Hexcode
        Data table sort indicator background color.
    data_table_hover_fg : Hexcode
        Data table hover foreground color.
    data_table_hover_bg : Hexcode
        Data table hover background color.
    data_table_stripe_fg : Hexcode
        Data table stripe foreground color.
    data_table_stripe_bg : Hexcode
        Data table stripe background color.
    data_table_stripe_hover_fg : Hexcode
        Data table stripe hover foreground color.
    data_table_stripe_hover_bg : Hexcode
        Data table stripe hover background color.
    data_table_selected_fg : Hexcode
        Data table selected foreground color.
    data_table_selected_bg : Hexcode
        Data table selected background color.
    data_table_selected_hover_fg : Hexcode
        Data table selected hover foreground color.
    data_table_selected_hover_bg : Hexcode
        Data table selected hover background color.
    progress_bar_fg : Hexcode
        Progress bar foreground color.
    progress_bar_bg : Hexcode
        Progress bar background color.
    markdown_link_fg : Hexcode
        Markdown link foreground color.
    markdown_link_bg : Hexcode
        Markdown link background color.
    markdown_link_hover_fg : Hexcode
        Markdown link hover foreground color.
    markdown_link_hover_bg : Hexcode
        Markdown link hover background color.
    markdown_inline_code_fg : Hexcode
        Markdown inline code foreground color.
    markdown_inline_code_bg : Hexcode
        Markdown inline code background color.
    markdown_quote_fg : Hexcode
        Markdown quote foreground color.
    markdown_quote_bg : Hexcode
        Markdown quote background color.
    markdown_title_fg : Hexcode
        Markdown title foreground color.
    markdown_title_bg : Hexcode
        Markdown title background color.
    markdown_image_fg : Hexcode
        Markdown image foreground color.
    markdown_image_bg : Hexcode
        Markdown image background color.
    markdown_block_code_background : Hexcode
        Markdown block code background color.
    markdown_quote_block_code_background : Hexcode
        Markdown quote block code background color.
    markdown_header_background : Hexcode
        Markdown header background color.
    scroll_view_scrollbar : Hexcode
        Scroll view scrollbar color.
    scroll_view_indicator_normal : Hexcode
        Scroll view indicator normal color.
    scroll_view_indicator_hover : Hexcode
        Scroll view indicator hover color.
    scroll_view_indicator_press : Hexcode
        Scroll view indicator press color.
    window_border_normal : Hexcode
        Window border normal color.
    window_border_inactive : Hexcode
        Window border inactive color.
    """

    primary_fg: Hexcode
    """The primary foreground color."""
    primary_bg: Hexcode
    """The primary background color."""
    text_pad_line_highlight_fg: Hexcode
    """Text pad line highlight foreground color."""
    text_pad_line_highlight_bg: Hexcode
    """Text pad line highlight background color."""
    text_pad_selection_highlight_fg: Hexcode
    """Text pad selection foreground color."""
    text_pad_selection_highlight_bg: Hexcode
    """Text pad selection background color."""
    textbox_primary_fg: Hexcode
    """Text pad primary foreground color."""
    textbox_primary_bg: Hexcode
    """Text pad primary background color."""
    textbox_selection_highlight_fg: Hexcode
    """Textbox selection foreground color."""
    textbox_selection_highlight_bg: Hexcode
    """Textbox selection background color."""
    textbox_placeholder_fg: Hexcode
    """Textbox placeholder foreground color."""
    textbox_placeholder_bg: Hexcode
    """Textbox placeholder background color."""
    button_normal_fg: Hexcode
    """Button normal foreground color."""
    button_normal_bg: Hexcode
    """Button normal background color."""
    button_hover_fg: Hexcode
    """Button hover foreground color."""
    button_hover_bg: Hexcode
    """Button hover background color."""
    button_press_fg: Hexcode
    """Button press foreground color."""
    button_press_bg: Hexcode
    """Button press background color."""
    button_disallowed_fg: Hexcode
    """Button disallowed foreground color."""
    button_disallowed_bg: Hexcode
    """Button disallowed background color."""
    menu_item_hover_fg: Hexcode
    """Menu item hover foreground color."""
    menu_item_hover_bg: Hexcode
    """Menu item hover background color."""
    menu_item_selected_fg: Hexcode
    """Menu item selected foreground color."""
    menu_item_selected_bg: Hexcode
    """Menu item selected background color."""
    menu_item_disallowed_fg: Hexcode
    """Menu item disallowed foreground color."""
    menu_item_disallowed_bg: Hexcode
    """Menu item disallowed background color."""
    titlebar_normal_fg: Hexcode
    """Titlebar normal foreground color."""
    titlebar_normal_bg: Hexcode
    """Titlebar normal background color."""
    titlebar_inactive_fg: Hexcode
    """Titlebar inactive foreground color."""
    titlebar_inactive_bg: Hexcode
    """Titlebar inactive background color."""
    data_table_sort_indicator_fg: Hexcode
    """Data table sort indicator foreground color."""
    data_table_sort_indicator_bg: Hexcode
    """Data table sort indicator background color."""
    data_table_hover_fg: Hexcode
    """Data table hover foreground color."""
    data_table_hover_bg: Hexcode
    """Data table hover background color."""
    data_table_stripe_fg: Hexcode
    """Data table stripe foreground color."""
    data_table_stripe_bg: Hexcode
    """Data table stripe background color."""
    data_table_stripe_hover_fg: Hexcode
    """Data table stripe hover foreground color."""
    data_table_stripe_hover_bg: Hexcode
    """Data table stripe hover background color."""
    data_table_selected_fg: Hexcode
    """Data table selected foreground color."""
    data_table_selected_bg: Hexcode
    """Data table selected background color."""
    data_table_selected_hover_fg: Hexcode
    """Data table selected hover foreground color."""
    data_table_selected_hover_bg: Hexcode
    """Data table selected hover background color."""
    progress_bar_fg: Hexcode
    """Progress bar foreground color."""
    progress_bar_bg: Hexcode
    """Progress bar background color."""
    markdown_link_fg: Hexcode
    """Markdown link foreground color."""
    markdown_link_bg: Hexcode
    """Markdown link background color."""
    markdown_link_hover_fg: Hexcode
    """Markdown link hover foreground color."""
    markdown_link_hover_bg: Hexcode
    """Markdown link hover background color."""
    markdown_inline_code_fg: Hexcode
    """Markdown inline code foreground color."""
    markdown_inline_code_bg: Hexcode
    """Markdown inline code background color."""
    markdown_quote_fg: Hexcode
    """Markdown quote foreground color."""
    markdown_quote_bg: Hexcode
    """Markdown quote background color."""
    markdown_title_fg: Hexcode
    """Markdown title foreground color."""
    markdown_title_bg: Hexcode
    """Markdown title background color."""
    markdown_image_fg: Hexcode
    """Markdown image foreground color."""
    markdown_image_bg: Hexcode
    """Markdown image background color."""
    markdown_block_code_bg: Hexcode
    """Markdown block code background color."""
    markdown_quote_block_code_bg: Hexcode
    """Markdown quote block code background color."""
    markdown_header_bg: Hexcode
    """Markdown header background color."""
    scroll_view_scrollbar: Hexcode
    """Scroll view scrollbar color."""
    scroll_view_indicator_normal: Hexcode
    """Scroll view indicator normal color."""
    scroll_view_indicator_hover: Hexcode
    """Scroll view indicator hover color."""
    scroll_view_indicator_press: Hexcode
    """Scroll view indicator press color."""
    window_border_normal: Hexcode
    """Window border normal color."""
    window_border_inactive: Hexcode
    """Window border inactive color."""
