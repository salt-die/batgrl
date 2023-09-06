"""
Commonly used colors.
"""
from .color_data_structures import *

__all__ = (
    "WHITE",
    "BLACK",
    "RED",
    "GREEN",
    "BLUE",
    "YELLOW",
    "CYAN",
    "MAGENTA",
    "AWHITE",
    "ABLACK",
    "ARED",
    "AGREEN",
    "ABLUE",
    "AYELLOW",
    "ACYAN",
    "AMAGENTA",
    "TRANSPARENT",
    "WHITE_ON_BLACK",
    "BLACK_ON_BLACK",
    "DEFAULT_COLOR_THEME",
)

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

WHITE_ON_BLACK = ColorPair.from_colors(WHITE, BLACK)
"""White on black color pair."""

BLACK_ON_BLACK = ColorPair.from_colors(BLACK, BLACK)
"""Black on black color pair."""

DEFAULT_COLOR_THEME = ColorTheme.from_hexes(
    primary="F6A7A9070C25",
    pad_line_highlight="F6A7A90C0E30",
    pad_selection_highlight="F6A7A90F1847",
    textbox_primary="FFF0F6070C25",
    textbox_selection_highlight="FFF0F60F1847",
    textbox_placeholder="2A3A92070C25",
    panel="4D67FF070C25",
    button_normal="DDE4ED2A3CA0",
    button_hover="FFF0F63248C0",
    button_press="FFF0F6c4a219",
    menu_item_hover="F6A7A9111834",
    menu_item_selected="ECF3FF1B244B",
    menu_item_disabled="272B40070C25",
    titlebar_normal="FFE0DF070C25",
    titlebar_inactive="7D6B71070C25",
    window_border_normal="122162FF",
    window_border_inactive="282C3EFF",
    scrollbar="070C25",
    scrollbar_indicator_normal="0E1843",
    scrollbar_indicator_hover="111E4F",
    scrollbar_indicator_press="172868",
    data_table_sort_indicator="ECF3FF070C25",
    data_table_hover="F6A7A9111834",
    data_table_stripe="F6A7A90B1238",
    data_table_stripe_hover="F6A7A90F184A",
    data_table_selected="ECF3FF1B244B",
    data_table_selected_hover="ECF3FF111F5E",
)
"""Default color theme."""
