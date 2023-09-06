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
    from_hex:
        Create a :class:`ColorPair` from a 12-digit hex code.
    from_hexes:
        Create a :class:`ColorPair` from two hex codes.
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
    def from_hex(cls, hexcode: str):
        """
        Create a :class:`ColorPair` from a 12-digit hex code.

        Parameters
        ----------
        hexcode : str
            Hex code for color pair.
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
    pad_line_highlight : ColorPair
        Text pad line highlight color pair.
    pad_selection_highlight : ColorPair
        Text pad selection highlight color pair.
    textbox_primary : ColorPair
        Textbox primary color pair.
    textbox_selection_highlight : ColorPair
        Textbox selection highlight color pair.
    textbox_placeholder : ColorPair
        Textbox placeholder text color pair.
    panel : ColorPair
        Text panel color pair.
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
    scrollbar : Color
        Scrollbar color.
    scrollbar_indicator_normal : Color
        Scrollbar indicator color.
    scrollbar_indicator_hover : Color
        Hovered scrollbar indicator color.
    scrollbar_indicator_press : Color
        Pressed scrollbar indicator color.
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

    Attributes
    ----------
    primary : ColorPair
        Primary color pair.
    pad_line_highlight : ColorPair
        Text pad line highlight color pair.
    pad_selection_highlight : ColorPair
        Text pad selection highlight color pair.
    textbox_primary : ColorPair
        Textbox primary color pair.
    textbox_selection_highlight : ColorPair
        Textbox selection highlight color pair.
    textbox_placeholder : ColorPair
        Textbox placeholder text color pair.
    panel : ColorPair
        Text panel color pair.
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
    scrollbar : Color
        Scrollbar color.
    scrollbar_indicator_normal : Color
        Scrollbar indicator color.
    scrollbar_indicator_hover : Color
        Hovered scrollbar indicator color.
    scrollbar_indicator_press : Color
        Pressed scrollbar indicator color.
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

    Methods
    -------
    from_hexes:
        Return a ColorTheme using hex codes.
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    primary: ColorPair
    pad_line_highlight: ColorPair
    pad_selection_highlight: ColorPair
    textbox_primary: ColorPair
    textbox_selection_highlight: ColorPair
    textbox_placeholder: ColorPair
    panel: ColorPair
    button_normal: ColorPair
    button_hover: ColorPair
    button_press: ColorPair
    menu_item_hover: ColorPair
    menu_item_selected: ColorPair
    menu_item_disabled: ColorPair
    titlebar_normal: ColorPair
    titlebar_inactive: ColorPair
    window_border_normal: AColor
    window_border_inactive: AColor
    scrollbar: Color
    scrollbar_indicator_normal: Color
    scrollbar_indicator_hover: Color
    scrollbar_indicator_press: Color
    data_table_sort_indicator: ColorPair
    data_table_hover: ColorPair
    data_table_stripe: ColorPair
    data_table_stripe_hover: ColorPair
    data_table_selected: ColorPair
    data_table_selected_hover: ColorPair

    @classmethod
    def from_hexes(
        cls,
        primary: str,
        panel: str,
        pad_line_highlight: str,
        pad_selection_highlight: str,
        textbox_primary: str,
        textbox_selection_highlight: str,
        textbox_placeholder: str,
        button_normal: str,
        button_hover: str,
        button_press: str,
        menu_item_hover: str,
        menu_item_selected: str,
        menu_item_disabled: str,
        titlebar_normal: str,
        titlebar_inactive: str,
        window_border_normal: str,
        window_border_inactive: str,
        scrollbar: str,
        scrollbar_indicator_normal: str,
        scrollbar_indicator_hover: str,
        scrollbar_indicator_press: str,
        data_table_sort_indicator: str,
        data_table_hover: str,
        data_table_stripe: str,
        data_table_stripe_hover: str,
        data_table_selected: str,
        data_table_selected_hover: str,
    ):
        """
        Return a ColorTheme using hex codes.

        ColorPair hex codes should be 12 digits.

        Parameters
        ----------
        primary : str
            Hex code for primary color pair.
        pad_line_highlight : str
            Hex code for text pad line highlight color pair.
        pad_selection_highlight : str
            Hex code for text pad selection highlight color pair.
        textbox_primary : str
            Hex code for textbox primary color pair.
        textbox_selection_highlight : str
            Hex code for textbox selection highlight color pair.
        textbox_placeholder : str
            Hex code for textbox placeholder text color pair.
        panel : str
            Hex code for text panel color pair.
        button_normal : str
            Hex code for button color pair.
        button_hover : str
            Hex code for hovored button color pair.
        button_press : str
            Hex code for pressed button color pair.
        menu_item_hover : str
            Hex code for hovered menu item color pair.
        menu_item_selected : str
            Hex code for selected menu item color pair.
        menu_item_disabled : str
            Hex code for disabled menu item color pair.
        titlebar_normal : str
            Hex code for titlebar color pair.
        titlebar_inactive : str
            Hex code for inactive titlebar color pair.
        window_border_normal : str
            Hex code for border color.
        window_border_inactive : str
            Hex code for inactive border color.
        scrollbar : str
            Hex code for scrollbar color.
        scrollbar_indicator_normal : str
            Hex code for scrollbar indicator color.
        scrollbar_indicator_hover : str
            Hex code for hovered scrollbar indicator color.
        scrollbar_indicator_press : str
            Hex code for pressed scrollbar indicator color.
        data_table_sort_indicator : str
            Hex code for color pair of sort indicator for a column label in a data table.
        data_table_hover : str
            Hex code for color pair of hovered items in a data table.
        data_table_stripe : str
            Hex code for color pair of striped items in a data table.
        data_table_stripe_hover : str
            Hex code for color pair of striped, hovered items in a data table.
        data_table_selected : str
            Hex code for color pair of selected items in a data table.
        data_table_selected_hover : str
            Hex code for color pair of selected, hovered items in a data table.
        """
        return cls(
            ColorPair.from_hex(primary),
            ColorPair.from_hex(pad_line_highlight),
            ColorPair.from_hex(pad_selection_highlight),
            ColorPair.from_hex(textbox_primary),
            ColorPair.from_hex(textbox_selection_highlight),
            ColorPair.from_hex(textbox_placeholder),
            ColorPair.from_hex(panel),
            ColorPair.from_hex(button_normal),
            ColorPair.from_hex(button_hover),
            ColorPair.from_hex(button_press),
            ColorPair.from_hex(menu_item_hover),
            ColorPair.from_hex(menu_item_selected),
            ColorPair.from_hex(menu_item_disabled),
            ColorPair.from_hex(titlebar_normal),
            ColorPair.from_hex(titlebar_inactive),
            AColor.from_hex(window_border_normal),
            AColor.from_hex(window_border_inactive),
            Color.from_hex(scrollbar),
            Color.from_hex(scrollbar_indicator_normal),
            Color.from_hex(scrollbar_indicator_hover),
            Color.from_hex(scrollbar_indicator_press),
            ColorPair.from_hex(data_table_sort_indicator),
            ColorPair.from_hex(data_table_hover),
            ColorPair.from_hex(data_table_stripe),
            ColorPair.from_hex(data_table_stripe_hover),
            ColorPair.from_hex(data_table_selected),
            ColorPair.from_hex(data_table_selected_hover),
        )