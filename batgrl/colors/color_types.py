"""Color data structures."""
from dataclasses import dataclass
from typing import NamedTuple

__all__ = [
    "AColor",
    "Color",
    "ColorPair",
    "ColorTheme",
]


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
    from_hex(hexcode):
        Create a :class:`Color` from a hex code.
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    """

    red: int
    green: int
    blue: int

    @classmethod
    def from_hex(cls, hexcode: str) -> "Color":
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
    from_hex(hexcode):
        Create an :class:`AColor` from a hex code.
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    """

    red: int
    green: int
    blue: int
    alpha: int = 255

    @classmethod
    def from_hex(cls, hexcode: str) -> "AColor":
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
        hexcode = hexcode.removeprefix("#")

        if len(hexcode) not in (6, 8):
            raise ValueError(f"{hexcode!r} is not a valid hex code")

        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:6], 16),
            int(hexcode[6:] or "ff", 16),
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
    from_colors(fg_color, bg_color):
        Create a :class:`ColorPair` from two colors.
    from_hex(hexcode):
        Create a :class:`ColorPair` from a 12-digit hex code.
    from_hexes(fg_hexcode, bg_hexcode):
        Create a :class:`ColorPair` from two hex codes.
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    reversed():
        Return a :class:`ColorPair` with the foreground and background reversed.
    """

    fg_red: int
    fg_green: int
    fg_blue: int
    bg_red: int
    bg_green: int
    bg_blue: int

    @classmethod
    def from_colors(
        cls, fg_color: Color | AColor, bg_color: Color | AColor
    ) -> "ColorPair":
        """
        Create a :class:`ColorPair` from two colors.

        Parameters
        ----------
        fg_color : Color | AColor
            Foreground color.
        bg_color : Color | AColor
            Background color.

        Returns
        -------
        ColorPair
            A new color pair.
        """
        return cls(*fg_color[:3], *bg_color[:3])

    @classmethod
    def from_hex(cls, hexcode: str) -> "ColorPair":
        """
        Create a :class:`ColorPair` from a 12-digit hex code.

        Parameters
        ----------
        hexcode : str
            Hex code for color pair.

        Returns
        -------
        ColorPair
            A new color pair.
        """
        return cls(
            int(hexcode[:2], 16),
            int(hexcode[2:4], 16),
            int(hexcode[4:6], 16),
            int(hexcode[6:8], 16),
            int(hexcode[8:10], 16),
            int(hexcode[10:12], 16),
        )

    @classmethod
    def from_hexes(cls, fg_hexcode: str, bg_hexcode: str) -> "ColorPair":
        """
        Create a :class:`ColorPair` from two hex codes.

        Parameters
        ----------
        fg_hexcode : int | str
            Hex code for foreground color.
        bg_hexcode : int | str
            Hex code for background color.

        Returns
        -------
        ColorPair
            A new color pair.
        """
        return cls(
            int(fg_hexcode[:2], 16),
            int(fg_hexcode[2:4], 16),
            int(fg_hexcode[4:6], 16),
            int(bg_hexcode[:2], 16),
            int(bg_hexcode[2:4], 16),
            int(bg_hexcode[4:6], 16),
        )

    @property
    def fg_color(self) -> Color:
        """The foreground color."""
        return Color(*self[:3])

    @property
    def bg_color(self) -> Color:
        """The background color."""
        return Color(*self[3:])

    def reversed(self) -> "ColorPair":
        """
        Return a :class:`ColorPair` with the foreground and background reversed.

        Returns
        -------
        ColorPair
            A new color pair with colors foreground and background reversed.
        """
        return ColorPair.from_colors(self.bg_color, self.fg_color)


@dataclass(slots=True, frozen=True, kw_only=True)
class ColorTheme:
    """
    Colors for themable gadgets.

    Parameters
    ----------
    primary : ColorPair, default: ColorPair(246, 167, 169, 7, 12, 37)
        Primary color pair.
    text_pad_line_highlight : ColorPair, default: ColorPair(246, 167, 169, 12, 14, 48)
        Text pad line highlight color pair.
    text_pad_selection_highlight : ColorPair, default: ColorPair(246, 167, 169, 15, 24, 71)
        Text pad selection highlight color pair.
    textbox_primary : ColorPair, default: ColorPair(255, 240, 246, 7, 12, 37)
        Textbox primary color pair.
    textbox_selection_highlight : ColorPair, default: ColorPair(255, 240, 246, 15, 24, 71)
        Textbox selection highlight color pair.
    textbox_placeholder : ColorPair, default: ColorPair(42, 58, 146, 7, 12, 37)
        Textbox placeholder text color pair.
    button_normal : ColorPair, default: ColorPair(221, 228, 237, 42, 60, 160)
        Button color pair.
    button_hover : ColorPair, default: ColorPair(255, 240, 246, 50, 72, 192)
        Hovored button color pair.
    button_press : ColorPair, default: ColorPair(255, 240, 246, 196, 162, 25)
        Pressed button color pair.
    menu_item_hover : ColorPair, default: ColorPair(246, 167, 169, 17, 24, 52)
        Hovered menu item color pair.
    menu_item_selected : ColorPair, default: ColorPair(236, 243, 255, 27, 36, 75)
        Selected menu item color pair.
    menu_item_disabled : ColorPair, default: ColorPair(39, 43, 64, 7, 12, 37)
        Disabled menu item color pair.
    titlebar_normal : ColorPair, default: ColorPair(255, 224, 223, 7, 12, 37)
        Titlebar color pair.
    titlebar_inactive : ColorPair, default: ColorPair(125, 107, 113, 7, 12, 37)
        Inactive titlebar color pair.
    window_border_normal : AColor, default: AColor(18, 33, 98, 255)
        Border color.
    window_border_inactive : AColor, default: AColor(40, 44, 62, 255)
        Inactive border color.
    data_table_sort_indicator : ColorPair, default: ColorPair(236, 243, 255, 7, 12, 37)
        Color pair of sort indicator for a column label in a data table.
    data_table_hover : ColorPair, default: ColorPair(246, 167, 169, 17, 24, 52)
        Color pair of hovered items in a data table.
    data_table_stripe : ColorPair, default: ColorPair(246, 167, 169, 11, 18, 56)
        Color pair of striped items in a data table.
    data_table_stripe_hover : ColorPair, default: ColorPair(246, 167, 169, 15, 24, 74)
        Color pair of striped, hovered items in a data table.
    data_table_selected : ColorPair, default: ColorPair(236, 243, 255, 17, 31, 94)
        Color pair of selected items in a data table.
    data_table_selected_hover : ColorPair, default: ColorPair(236, 243, 255, 27, 36, 75)
        Color pair of selected, hovered items in a data table.
    progress_bar : ColorPair, default: ColorPair(255, 224, 223, 42, 60, 160)
        Color pair of progress bar.
    scroll_view_scrollbar : Color, default: Color(7, 12, 37)
        Color of scrollbar in a scroll view.
    scroll_view_indicator_normal : Color, default: Color(14, 24, 67)
        Color of indicator in a scroll view.
    scroll_view_indicator_hover : Color, default: Color(17, 30, 79)
        Color of hovered indicator in a scroll view.
    scroll_view_indicator_press : Color, default: Color(23, 40, 104)
        Color of pressed indicator in a scroll view.
    markdown_link : ColorPair, default: ColorPair(55, 108, 255, 7, 12, 37)
        Color pair of markdown link.
    markdown_link_hover : ColorPair, default: ColorPair(70, 104, 255, 7, 12, 37)
        Color pair of hovered markdown link.
    markdown_inline_code : ColorPair, default: ColorPair(128, 106, 229, 8, 11, 26)
        Color pair of markdown inline code.
    markdown_quote : ColorPair, default: ColorPair(32, 84, 226, 12, 27, 75)
        Color pair of markdown quote.
    markdown_title : ColorPair, default: ColorPair(207, 209, 212, 41, 42, 45)
        Color pair of markdown title.
    markdown_image : ColorPair, default: ColorPair(246, 167, 169, 12, 21, 64)
        Color pair of markdown image.
    markdown_block_code_background : Color, default: Color(8, 11, 26)
        Color of markdown block code background.
    markdown_quote_block_code_background : Color, default: Color(17, 38, 93)
        Color of markdown quoted block code background.
    markdown_header_background : Color, default: Color(3, 6, 18)
        Color of markdown header color.

    Attributes
    ----------
    primary : ColorPair
        Primary color pair.
    text_pad_line_highlight : ColorPair
        Text pad line highlight color pair.
    text_pad_selection_highlight : ColorPair
        Text pad selection highlight color pair.
    textbox_primary : ColorPair
        Textbox primary color pair.
    textbox_selection_highlight : ColorPair
        Textbox selection highlight color pair.
    textbox_placeholder : ColorPair
        Textbox placeholder text color pair.
    button_normal : ColorPair
        Button color pair.
    button_hover : ColorPair
        Hovored button color pair.
    button_press : ColorPair
        Pressed button color pair.
    menu_item_hover : ColorPair
        Hovered menu item color pair.
    menu_item_selected : ColorPair
        Selected menu item color pair.
    menu_item_disabled : ColorPair
        Disabled menu item color pair.
    titlebar_normal : ColorPair
        Titlebar color pair.
    titlebar_inactive : ColorPair
        Inactive titlebar color pair.
    window_border_normal : AColor
        Border color.
    window_border_inactive : AColor
        Inactive border color.
    data_table_sort_indicator : ColorPair
        Color pair of sort indicator for a column label in a data table.
    data_table_hover : ColorPair
        Color pair of hovered items in a data table.
    data_table_stripe : ColorPair
        Color pair of striped items in a data table.
    data_table_stripe_hover : ColorPair
        Color pair of striped, hovered items in a data table.
    data_table_selected : ColorPair
        Color pair of selected items in a data table.
    data_table_selected_hover : ColorPair
        Color pair of selected, hovered items in a data table.
    progress_bar : ColorPair
        Color pair of progress bar.
    scroll_view_scrollbar : Color
        Color of scrollbar in a scroll view.
    scroll_view_indicator_normal : Color
        Color of indicator in a scroll view.
    scroll_view_indicator_hover : Color
        Color of hovered indicator in a scroll view.
    scroll_view_indicator_press : Color
        Color of pressed indicator in a scroll view.
    markdown_link : ColorPair
        Color pair of markdown link.
    markdown_link_hover : ColorPair
        Color pair of hovered markdown link.
    markdown_inline_code : ColorPair
        Color pair of markdown inline code.
    markdown_quote : ColorPair
        Color pair of markdown quote.
    markdown_title : ColorPair
        Color pair of markdown title.
    markdown_image : ColorPair
        Color pair of markdown image.
    markdown_block_code_background : Color
        Color of markdown block code background.
    markdown_quote_block_code_background : Color
        Color of markdown quoted block code background.
    markdown_header_background : Color
        Color of markdown header color.
    """  # noqa

    primary: ColorPair = ColorPair(246, 167, 169, 7, 12, 37)
    text_pad_line_highlight: ColorPair = ColorPair(246, 167, 169, 12, 14, 48)
    text_pad_selection_highlight: ColorPair = ColorPair(246, 167, 169, 15, 24, 71)
    textbox_primary: ColorPair = ColorPair(255, 240, 246, 7, 12, 37)
    textbox_selection_highlight: ColorPair = ColorPair(255, 240, 246, 15, 24, 71)
    textbox_placeholder: ColorPair = ColorPair(42, 58, 146, 7, 12, 37)
    button_normal: ColorPair = ColorPair(221, 228, 237, 42, 60, 160)
    button_hover: ColorPair = ColorPair(255, 240, 246, 50, 72, 192)
    button_press: ColorPair = ColorPair(255, 240, 246, 196, 162, 25)
    menu_item_hover: ColorPair = ColorPair(246, 167, 169, 17, 24, 52)
    menu_item_selected: ColorPair = ColorPair(236, 243, 255, 27, 36, 75)
    menu_item_disabled: ColorPair = ColorPair(39, 43, 64, 7, 12, 37)
    titlebar_normal: ColorPair = ColorPair(255, 224, 223, 7, 12, 37)
    titlebar_inactive: ColorPair = ColorPair(125, 107, 113, 7, 12, 37)
    window_border_normal: AColor = AColor(18, 33, 98, 255)
    window_border_inactive: AColor = AColor(40, 44, 62, 255)
    data_table_sort_indicator: ColorPair = ColorPair(236, 243, 255, 7, 12, 37)
    data_table_hover: ColorPair = ColorPair(246, 167, 169, 17, 24, 52)
    data_table_stripe: ColorPair = ColorPair(246, 167, 169, 11, 18, 56)
    data_table_stripe_hover: ColorPair = ColorPair(246, 167, 169, 15, 24, 74)
    data_table_selected: ColorPair = ColorPair(236, 243, 255, 17, 31, 94)
    data_table_selected_hover: ColorPair = ColorPair(236, 243, 255, 27, 36, 75)
    progress_bar: ColorPair = ColorPair(255, 224, 223, 42, 60, 160)
    scroll_view_scrollbar: Color = Color(7, 12, 37)
    scroll_view_indicator_normal: Color = Color(14, 24, 67)
    scroll_view_indicator_hover: Color = Color(17, 30, 79)
    scroll_view_indicator_press: Color = Color(23, 40, 104)
    markdown_link: ColorPair = ColorPair(55, 108, 255, 7, 12, 37)
    markdown_link_hover: ColorPair = ColorPair(70, 104, 255, 7, 12, 37)
    markdown_inline_code: ColorPair = ColorPair(128, 106, 229, 8, 11, 26)
    markdown_quote: ColorPair = ColorPair(32, 84, 226, 12, 27, 75)
    markdown_title: ColorPair = ColorPair(207, 209, 212, 41, 42, 45)
    markdown_image: ColorPair = ColorPair(246, 167, 169, 12, 21, 64)
    markdown_block_code_background: Color = Color(8, 11, 26)
    markdown_quote_block_code_background: Color = Color(17, 38, 93)
    markdown_header_background: Color = Color(3, 6, 18)
