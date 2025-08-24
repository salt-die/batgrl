"""Color data structures."""

import re
from dataclasses import dataclass
from typing import Final, Literal, NamedTuple, Self

from .._style import Style

__all__ = ["AColor", "Color", "ColorTheme", "SyntaxHighlightTheme"]

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


type ColorThemeColor = Literal[
    "primary_fg",
    "primary_bg",
    "text_pad_line_highlight_fg",
    "text_pad_line_highlight_bg",
    "text_pad_selection_highlight_fg",
    "text_pad_selection_highlight_bg",
    "textbox_primary_fg",
    "textbox_primary_bg",
    "textbox_selection_highlight_fg",
    "textbox_selection_highlight_bg",
    "textbox_placeholder_fg",
    "textbox_placeholder_bg",
    "button_normal_fg",
    "button_normal_bg",
    "button_hover_fg",
    "button_hover_bg",
    "button_press_fg",
    "button_press_bg",
    "button_disallowed_fg",
    "button_disallowed_bg",
    "menu_item_hover_fg",
    "menu_item_hover_bg",
    "menu_item_selected_fg",
    "menu_item_selected_bg",
    "menu_item_disallowed_fg",
    "menu_item_disallowed_bg",
    "titlebar_normal_fg",
    "titlebar_normal_bg",
    "titlebar_inactive_fg",
    "titlebar_inactive_bg",
    "data_table_sort_indicator_fg",
    "data_table_sort_indicator_bg",
    "data_table_hover_fg",
    "data_table_hover_bg",
    "data_table_stripe_fg",
    "data_table_stripe_bg",
    "data_table_stripe_hover_fg",
    "data_table_stripe_hover_bg",
    "data_table_selected_fg",
    "data_table_selected_bg",
    "data_table_selected_hover_fg",
    "data_table_selected_hover_bg",
    "progress_bar_fg",
    "progress_bar_bg",
    "markdown_link_fg",
    "markdown_link_bg",
    "markdown_link_hover_fg",
    "markdown_link_hover_bg",
    "markdown_inline_code_fg",
    "markdown_inline_code_bg",
    "markdown_quote_fg",
    "markdown_quote_bg",
    "markdown_title_fg",
    "markdown_title_bg",
    "markdown_image_fg",
    "markdown_image_bg",
    "markdown_block_code_bg",
    "markdown_quote_block_code_bg",
    "markdown_header_bg",
    "scroll_view_scrollbar",
    "scroll_view_indicator_normal",
    "scroll_view_indicator_hover",
    "scroll_view_indicator_press",
    "window_border_normal",
    "window_border_inactive",
]

type ColorTheme = dict[ColorThemeColor, Hexcode]
"""
Colors for themable gadgets.

Missing colors will use the default color theme.
"""


@dataclass
class SyntaxHighlightTheme:
    """Syntax highlight theme."""

    default_fg: Color
    """Default foreground color."""
    default_bg: Color
    """Default background color."""
    cursor_fg: Color
    """Default cursor foreground color."""
    cursor_bg: Color
    """Default cursor background color."""
    active_line: Color
    """The background color of the cursor's current line."""
    selection: Color
    """The background color of selected text."""
    highlights: dict[str, tuple[Style, Color | None]]
    """A dictionary of tree sitter query names to (style, Color) tuples."""

    def __init__(
        self,
        default_fg: Hexcode,
        default_bg: Hexcode,
        cursor_fg: Hexcode,
        cursor_bg: Hexcode,
        active_line: Hexcode,
        selection: Hexcode,
        highlights: dict[str, tuple[Style, Hexcode | None]],
    ):
        self.default_fg = Color.from_hex(default_fg)
        self.default_bg = Color.from_hex(default_bg)
        self.cursor_fg = Color.from_hex(cursor_fg)
        self.cursor_bg = Color.from_hex(cursor_bg)
        self.active_line = Color.from_hex(active_line)
        self.selection = Color.from_hex(selection)
        self.highlights = {
            k: (style, None if hexcode is None else Color.from_hex(hexcode))
            for k, (style, hexcode) in highlights.items()
        }
