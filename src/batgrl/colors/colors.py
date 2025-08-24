"""Commonly used colors."""

from typing import Final

from .._style import Style
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
    default_fg="#f6a7a9",
    default_bg="#070c25",
    cursor_fg="#070c25",
    cursor_bg="#5268e6",
    active_line="#0d0e30",
    selection="#101847",
    highlights={
        "attribute": (Style.NO_STYLE, "#d4864d"),
        "bold": (Style.BOLD, None),
        "comment": (Style.NO_STYLE, "#554492"),
        "comment.documentation": (Style.NO_STYLE, "#4876db"),
        "comment.error": (Style.NO_STYLE, "#d6452b"),
        "comment.note": (Style.NO_STYLE, "#90cf5c"),
        "comment.todo": (Style.NO_STYLE, "#4eb8d8"),
        "comment.warning": (Style.NO_STYLE, "#d37f11"),
        "conditional": (Style.NO_STYLE, "#5bb177"),
        "constant": (Style.BOLD, "#91a5Bd"),
        "constant.builtin": (Style.BOLD, "#17c78c"),
        "constant.builtin.boolean": (Style.BOLD, "#17b865"),
        "constant.character": (Style.BOLD, "#17c78c"),
        "constant.macro": (Style.BOLD, "#7eb0ec"),
        "constructor": (Style.BOLD, "#de9138"),
        "escape": (Style.NO_STYLE, "#17c78c"),
        "error": (Style.NO_STYLE, "#c71726"),
        "exception": (Style.NO_STYLE, "#3db177"),
        "float": (Style.NO_STYLE, "#e47559"),
        "function": (Style.NO_STYLE, "#cb5757"),
        "function.builtin": (Style.BOLD, "#d15656"),
        "function.call": (Style.NO_STYLE, "#cb5757"),
        "function.special": (Style.NO_STYLE, "#d85757"),
        "import": (Style.NO_STYLE, "#6180b3"),
        "include": (Style.NO_STYLE, "#6180b3"),
        "italic": (Style.ITALIC, None),
        "keyword": (Style.NO_STYLE, "#17b865"),
        "keyword.class": (Style.NO_STYLE, "#c75974"),
        "keyword.conditional": (Style.NO_STYLE, "#5bb177"),
        "keyword.directive": (Style.NO_STYLE, "#e9dfcc"),
        "keyword.function": (Style.NO_STYLE, "#c75974"),
        "keyword.modifier": (Style.NO_STYLE, "#b96772"),
        "keyword.operator": (Style.NO_STYLE, "#c76f6f"),
        "keyword.repeat": (Style.NO_STYLE, "#5bb177"),
        "keyword.return": (Style.NO_STYLE, "#5bb177"),
        "keyword.type": (Style.BOLD, "#de9138"),
        "method": (Style.NO_STYLE, "#cb5757"),
        "method.call": (Style.NO_STYLE, "#cb5757"),
        "number": (Style.NO_STYLE, "#e47559"),
        "operator": (Style.NO_STYLE, "#c76f6f"),
        "parameter": (Style.NO_STYLE, "#ce967c"),
        "property": (Style.NO_STYLE, "#fdc0be"),
        "punctuation": (Style.NO_STYLE, "#ce967c"),
        "punctuation.bracket": (Style.NO_STYLE, "#a73e3e"),
        "punctuation.delimiter": (Style.NO_STYLE, "#ce967c"),
        "punctuation.special": (Style.NO_STYLE, "#ce967c"),
        "repeat": (Style.NO_STYLE, "#5bb177"),
        "strikethrough": (Style.STRIKETHROUGH, None),
        "string": (Style.NO_STYLE, "#da7763"),
        "string.documentation": (Style.NO_STYLE, "#4876db"),
        "string.escape": (Style.NO_STYLE, "#17c78c"),
        "string.special.url": (Style.UNDERLINE, None),
        "type": (Style.BOLD, "#de9138"),
        "type.builtin": (Style.BOLD, "#de9138"),
        "type.class": (Style.BOLD, "#de9138"),
        "type.enum": (Style.BOLD, "#a076b9"),
        "variable": (Style.NO_STYLE, "#fdc0be"),
        "variable.builtin": (Style.NO_STYLE, "#c68a6d"),
        "variable.parameter": (Style.NO_STYLE, "#d38a6d"),
    },
)
