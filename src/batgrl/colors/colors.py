"""Commonly used colors."""

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
    "DEFAULT_COLOR_THEME",
    "DEFAULT_PRIMARY_BG",
    "DEFAULT_PRIMARY_FG",
    "GREEN",
    "MAGENTA",
    "RED",
    "TRANSPARENT",
    "WHITE",
    "YELLOW",
    "Neptune",
]

WHITE = Color(255, 255, 255)
"""White."""

BLACK = Color(0, 0, 0)
"""Black."""

RED = Color(255, 0, 0)
"""Red."""

GREEN = Color(0, 255, 0)
"""Green."""

BLUE = Color(0, 0, 255)
"""Blue."""

YELLOW = Color(255, 255, 0)
"""Yellow."""

CYAN = Color(0, 255, 255)
"""Cyan."""

MAGENTA = Color(255, 0, 255)
"""Magenta."""

AWHITE = AColor(255, 255, 255)
"""Opaque white."""

ABLACK = AColor(0, 0, 0)
"""Opaque black."""

ARED = AColor(255, 0, 0)
"""Opaque red."""

AGREEN = AColor(0, 255, 0)
"""Opaque green."""

ABLUE = AColor(0, 0, 255)
"""Opaque blue."""

AYELLOW = AColor(255, 255, 0)
"""Opaque yellow."""

ACYAN = AColor(0, 255, 255)
"""Opaque cyan."""

AMAGENTA = AColor(255, 0, 255)
"""Opaque magenta."""

TRANSPARENT = AColor(0, 0, 0, 0)
"""Transparent black."""

DEFAULT_COLOR_THEME: ColorTheme = {
    "primary": {"fg": "f6a7a9", "bg": "070c25"},
    "text_pad_line_highlight": {"fg": "f6a7a9", "bg": "0c0e30"},
    "text_pad_selection_highlight": {"fg": "f6a7a9", "bg": "0f1847"},
    "textbox_primary": {"fg": "fff0f6", "bg": "070c25"},
    "textbox_selection_highlight": {"fg": "fff0f6", "bg": "0f1847"},
    "textbox_placeholder": {"fg": "2a3a92", "bg": "070c25"},
    "button_normal": {"fg": "dde4ed", "bg": "2a3ca0"},
    "button_hover": {"fg": "fff0f6", "bg": "3248c0"},
    "button_press": {"fg": "fff0f6", "bg": "c4a219"},
    "button_disallowed": {"fg": "272b40", "bg": "070c25"},
    "menu_item_hover": {"fg": "f2babc", "bg": "111834"},
    "menu_item_selected": {"fg": "ecf3ff", "bg": "1b244b"},
    "menu_item_disallowed": {"fg": "272b40", "bg": "070c25"},
    "titlebar_normal": {"fg": "ffe0df", "bg": "070c25"},
    "titlebar_inactive": {"fg": "7d6b71", "bg": "070c25"},
    "data_table_sort_indicator": {"fg": "ecf3ff", "bg": "070c25"},
    "data_table_hover": {"fg": "f6a7a9", "bg": "111834"},
    "data_table_stripe": {"fg": "f6a7a9", "bg": "0b1238"},
    "data_table_stripe_hover": {"fg": "f6a7a9", "bg": "0f184a"},
    "data_table_selected": {"fg": "ecf3ff", "bg": "111f5e"},
    "data_table_selected_hover": {"fg": "ecf3ff", "bg": "1b244b"},
    "progress_bar": {"fg": "ffe0df", "bg": "2a3ca0"},
    "markdown_link": {"fg": "376cff", "bg": "070c25"},
    "markdown_link_hover": {"fg": "4668ff", "bg": "070c25"},
    "markdown_inline_code": {"fg": "806ae5", "bg": "080b1a"},
    "markdown_quote": {"fg": "2054e2", "bg": "0c1b4b"},
    "markdown_title": {"fg": "cfd1d4", "bg": "292a2d"},
    "markdown_image": {"fg": "f6a7a9", "bg": "0c1540"},
    "markdown_block_code_background": "080b1a",
    "markdown_quote_block_code_background": "11265d",
    "markdown_header_background": "030612",
    "scroll_view_scrollbar": "070c25",
    "scroll_view_indicator_normal": "0e1843",
    "scroll_view_indicator_hover": "111e4f",
    "scroll_view_indicator_press": "172868",
    "window_border_normal": "122162",
    "window_border_inactive": "282c3e",
}
"""Default color theme."""

DEFAULT_PRIMARY_FG = Color.from_hex("f6a7a9")
"""Default primary foreground color."""

DEFAULT_PRIMARY_BG = Color.from_hex("070c25")
"""Default primary background color."""


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
