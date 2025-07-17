"""Commonly used colors."""

from typing import Final

from .color_types import AColor, Color, ColorTheme, SyntaxHighlightTheme

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
    "primary_fg": "#f6a7a9",
    "primary_bg": "#070c25",
    "text_pad_line_highlight_fg": "#f6a7a9",
    "text_pad_line_highlight_bg": "#0c0e30",
    "text_pad_selection_highlight_fg": "#f6a7a9",
    "text_pad_selection_highlight_bg": "#0f1847",
    "textbox_primary_fg": "#fff0f6",
    "textbox_primary_bg": "#070c25",
    "textbox_selection_highlight_fg": "#fff0f6",
    "textbox_selection_highlight_bg": "#0f1847",
    "textbox_placeholder_fg": "#2a3a92",
    "textbox_placeholder_bg": "#070c25",
    "button_normal_fg": "#dde4ed",
    "button_normal_bg": "#2a3ca0",
    "button_hover_fg": "#fff0f6",
    "button_hover_bg": "#3248c0",
    "button_press_fg": "#fff0f6",
    "button_press_bg": "#c4a219",
    "button_disallowed_fg": "#272b40",
    "button_disallowed_bg": "#070c25",
    "menu_item_hover_fg": "#f2babc",
    "menu_item_hover_bg": "#111834",
    "menu_item_selected_fg": "#ecf3ff",
    "menu_item_selected_bg": "#1b244b",
    "menu_item_disallowed_fg": "#272b40",
    "menu_item_disallowed_bg": "#070c25",
    "titlebar_normal_fg": "#ffe0df",
    "titlebar_normal_bg": "#070c25",
    "titlebar_inactive_fg": "#7d6b71",
    "titlebar_inactive_bg": "#070c25",
    "data_table_sort_indicator_fg": "#ecf3ff",
    "data_table_sort_indicator_bg": "#070c25",
    "data_table_hover_fg": "#f6a7a9",
    "data_table_hover_bg": "#111834",
    "data_table_stripe_fg": "#f6a7a9",
    "data_table_stripe_bg": "#0b1238",
    "data_table_stripe_hover_fg": "#f6a7a9",
    "data_table_stripe_hover_bg": "#0f184a",
    "data_table_selected_fg": "#ecf3ff",
    "data_table_selected_bg": "#111f5e",
    "data_table_selected_hover_fg": "#ecf3ff",
    "data_table_selected_hover_bg": "#1b244b",
    "progress_bar_fg": "#ffe0df",
    "progress_bar_bg": "#2a3ca0",
    "markdown_link_fg": "#376cff",
    "markdown_link_bg": "#070c25",
    "markdown_link_hover_fg": "#4668ff",
    "markdown_link_hover_bg": "#070c25",
    "markdown_inline_code_fg": "#806ae5",
    "markdown_inline_code_bg": "#080b1a",
    "markdown_quote_fg": "#2054e2",
    "markdown_quote_bg": "#0c1b4b",
    "markdown_title_fg": "#cfd1d4",
    "markdown_title_bg": "#292a2d",
    "markdown_image_fg": "#f6a7a9",
    "markdown_image_bg": "#0c1540",
    "markdown_block_code_bg": "#080b1a",
    "markdown_quote_block_code_bg": "#11265d",
    "markdown_header_bg": "#030612",
    "scroll_view_scrollbar": "#070c25",
    "scroll_view_indicator_normal": "#0e1843",
    "scroll_view_indicator_hover": "#111e4f",
    "scroll_view_indicator_press": "#172868",
    "window_border_normal": "#122162",
    "window_border_inactive": "#282c3e",
}
"""Neptune color theme."""

NEPTUNE_PRIMARY_FG: Final = Color.from_hex(NEPTUNE_THEME["primary_fg"])
"""The primary foreground color for the Neptune color theme."""

NEPTUNE_PRIMARY_BG: Final = Color.from_hex(NEPTUNE_THEME["primary_bg"])
"""The primary background color for the Neptune color theme."""

Neptune = SyntaxHighlightTheme(
    default_fg="#fdc0be",
    default_bg="#070c25",
    cursor_fg="#070c25",
    cursor_bg="#5268e6",
    active_line="#0d0e30",
    selection="#101847",
    highlights={
        "string": (0, "#da7763"),
        "comment": (0, "#554492"),
        "keyword": (0, "#17b865"),
        "operator": (0, "#ce967c"),
        "repeat": (0, "#5bb177"),
        "exception": (0, "#3db177"),
        "include": (0, "#6180b3"),
        "keyword.function": (0, "#c75974"),
        "keyword.return": (0, "#5bb177"),
        "keyword.operator": (0, "#dd982f"),
        "conditional": (0, "#5bb177"),
        "number": (0, "#e47559"),
        "float": (0, "#e47559"),
        "type": (1, "#de9138"),
        "type.class": (1, "#de9138"),
        "type.builtin": (1, "#de9138"),
        "constructor": (1, "#de9138"),
        "variable": (0, "#fdc0be"),
        "variable.builtin": (0, "#c68a6d"),
        "function": (0, "#cb5757"),
        "function.call": (0, "#cb5757"),
        "function.builtin": (1, "#d15656"),
        "method": (0, "#cb5757"),
        "method.call": (0, "#cb5757"),
        "boolean": (0, "#17b865"),
        "constant": (1, "#91a5Bd"),
        "constant.builtin": (1, "#17c78c"),
        "bold": (1, None),
        "italic": (2, None),
        "strikethrough": (8, None),
        "punctuation.bracket": (0, "#a73e3e"),
        "punctuation.delimiter": (0, "#a73e3e"),
        "punctuation.special": (0, "#ce967c"),
    },
)
