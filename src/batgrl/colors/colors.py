"""Commonly used colors."""

from typing import Final

from pygments.style import Style
from pygments.token import (
    Comment,
    Error,
    Generic,
    Keyword,
    Literal,
    Name,
    Number,
    Operator,
    String,
    Text,
    Token,
)

from .color_types import AColor, Color, ColorTheme

__all__ = [
    "ABLACK",
    "ABLUE",
    "ACYAN",
    "AGREEN",
    "AMAGENTA",
    "ARED",
    "AWHITE",
    "AYELLOW",
    "BLACK",
    "BLUE",
    "CYAN",
    "GREEN",
    "MAGENTA",
    "NEPTUNE_PRIMARY_BG",
    "NEPTUNE_PRIMARY_FG",
    "NEPTUNE_THEME",
    "RED",
    "TRANSPARENT",
    "WHITE",
    "YELLOW",
    "Neptune",
]

WHITE: Final = Color(255, 255, 255)
"""White."""

BLACK: Final = Color(0, 0, 0)
"""Black."""

RED: Final = Color(255, 0, 0)
"""Red."""

GREEN: Final = Color(0, 255, 0)
"""Green."""

BLUE: Final = Color(0, 0, 255)
"""Blue."""

YELLOW: Final = Color(255, 255, 0)
"""Yellow."""

CYAN: Final = Color(0, 255, 255)
"""Cyan."""

MAGENTA: Final = Color(255, 0, 255)
"""Magenta."""

AWHITE: Final = AColor(255, 255, 255)
"""Opaque white."""

ABLACK: Final = AColor(0, 0, 0)
"""Opaque black."""

ARED: Final = AColor(255, 0, 0)
"""Opaque red."""

AGREEN: Final = AColor(0, 255, 0)
"""Opaque green."""

ABLUE: Final = AColor(0, 0, 255)
"""Opaque blue."""

AYELLOW: Final = AColor(255, 255, 0)
"""Opaque yellow."""

ACYAN: Final = AColor(0, 255, 255)
"""Opaque cyan."""

AMAGENTA: Final = AColor(255, 0, 255)
"""Opaque magenta."""

TRANSPARENT: Final = AColor(0, 0, 0, 0)
"""Transparent black."""

NEPTUNE_THEME: Final[ColorTheme] = {
    "primary_fg": "f6a7a9",
    "primary_bg": "070c25",
    "text_pad_line_highlight_fg": "f6a7a9",
    "text_pad_line_highlight_bg": "0c0e30",
    "text_pad_selection_highlight_fg": "f6a7a9",
    "text_pad_selection_highlight_bg": "0f1847",
    "textbox_primary_fg": "fff0f6",
    "textbox_primary_bg": "070c25",
    "textbox_selection_highlight_fg": "fff0f6",
    "textbox_selection_highlight_bg": "0f1847",
    "textbox_placeholder_fg": "2a3a92",
    "textbox_placeholder_bg": "070c25",
    "button_normal_fg": "dde4ed",
    "button_normal_bg": "2a3ca0",
    "button_hover_fg": "fff0f6",
    "button_hover_bg": "3248c0",
    "button_press_fg": "fff0f6",
    "button_press_bg": "c4a219",
    "button_disallowed_fg": "272b40",
    "button_disallowed_bg": "070c25",
    "menu_item_hover_fg": "f2babc",
    "menu_item_hover_bg": "111834",
    "menu_item_selected_fg": "ecf3ff",
    "menu_item_selected_bg": "1b244b",
    "menu_item_disallowed_fg": "272b40",
    "menu_item_disallowed_bg": "070c25",
    "titlebar_normal_fg": "ffe0df",
    "titlebar_normal_bg": "070c25",
    "titlebar_inactive_fg": "7d6b71",
    "titlebar_inactive_bg": "070c25",
    "data_table_sort_indicator_fg": "ecf3ff",
    "data_table_sort_indicator_bg": "070c25",
    "data_table_hover_fg": "f6a7a9",
    "data_table_hover_bg": "111834",
    "data_table_stripe_fg": "f6a7a9",
    "data_table_stripe_bg": "0b1238",
    "data_table_stripe_hover_fg": "f6a7a9",
    "data_table_stripe_hover_bg": "0f184a",
    "data_table_selected_fg": "ecf3ff",
    "data_table_selected_bg": "111f5e",
    "data_table_selected_hover_fg": "ecf3ff",
    "data_table_selected_hover_bg": "1b244b",
    "progress_bar_fg": "ffe0df",
    "progress_bar_bg": "2a3ca0",
    "markdown_link_fg": "376cff",
    "markdown_link_bg": "070c25",
    "markdown_link_hover_fg": "4668ff",
    "markdown_link_hover_bg": "070c25",
    "markdown_inline_code_fg": "806ae5",
    "markdown_inline_code_bg": "080b1a",
    "markdown_quote_fg": "2054e2",
    "markdown_quote_bg": "0c1b4b",
    "markdown_title_fg": "cfd1d4",
    "markdown_title_bg": "292a2d",
    "markdown_image_fg": "f6a7a9",
    "markdown_image_bg": "0c1540",
    "markdown_block_code_bg": "080b1a",
    "markdown_quote_block_code_bg": "11265d",
    "markdown_header_bg": "030612",
    "scroll_view_scrollbar": "070c25",
    "scroll_view_indicator_normal": "0e1843",
    "scroll_view_indicator_hover": "111e4f",
    "scroll_view_indicator_press": "172868",
    "window_border_normal": "122162",
    "window_border_inactive": "282c3e",
}
"""Neptune color theme."""

NEPTUNE_PRIMARY_FG: Final = Color.from_hex(NEPTUNE_THEME["primary_fg"])
"""The primary foreground color for the Neptune color theme."""

NEPTUNE_PRIMARY_BG: Final = Color.from_hex(NEPTUNE_THEME["primary_bg"])
"""The primary background color for the Neptune color theme."""


class Neptune(Style):
    """
    Default syntax highlight color theme.

    This style is adapted from
    https://github.com/yl92/paddy-color-theme/blob/master/themes/upright/Paddy-neptune-upright-color-theme.json.
    """

    name = "neptune"

    background_color = "#070c25"
    highlight_color = "#5f32db"

    line_number_special_color = "#2f3adf"
    line_number_special_background_color = "#5f32db"

    line_number_color = "#527bff"
    line_number_background_color = "#070c25"

    styles = {
        Token: "#f6a7a9",
        Error: "bold #d32e11",
        Keyword: "#5bb177",
        Keyword.Constant: "bold #91a5bd",
        Keyword.Pseudo: "#e28f37",
        Name: "#f6a7a9",
        Name.Class: "bold #de9138",
        Name.Constant: "#17c78c",
        Name.Decorator: "#d85757",
        Name.Exception: "bold #de9138",
        Name.Function: "#d85757",
        Name.Label: "#f6a7a9",
        Name.Property: "#f6a7a9",
        Name.Tag: "bold #309388",
        Name.Variable: "#f6a7a9",
        Literal: "#da7763",
        String: "#da7763",
        String.Affix: "#c75974",
        String.Escape: "#62A594",
        String.Regex: "#d46fbe",
        Number: "#e47559",
        Comment: "#554492",
        Comment.Special: "#978d7a",
        Operator: "#5bb177",
        Generic: "#f6a7a9",
        Generic.Deleted: "bold bg:#cf5076 #309388",
        Generic.Emph: "italic",
        Generic.Error: "bold #d32e11",
        Generic.Heading: "#da5656",
        Generic.Inserted: "bg:#4d67ff #da7763",
        Generic.Output: "#69a097",
        Generic.Strong: "bold",
        Generic.EmphStrong: "bold italic",
        Generic.Subheading: "#da5656",
        Generic.Traceback: "bold #de9138",
        Generic.Underline: "underline",
        Text: "#f6a7a9",
    }
