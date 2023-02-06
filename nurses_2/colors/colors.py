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

DEFAULT_COLOR_THEME = ColorTheme(
    primary=ColorPair.from_hexes("F6A7A9", "070C25"),
    panel=ColorPair.from_hexes("4D67FF", "070C25"),
    button_normal=ColorPair.from_hexes("DDE4ED", "2A3CA0"),
    button_hover=ColorPair.from_hexes("FFF0F6", "3248C0"),
    button_press=ColorPair.from_hexes("FFF0F6", "c4a219"),
    item_hover=ColorPair.from_hexes("F6A7A9", "111834"),
    item_selected=ColorPair.from_hexes("ECF3FF", "1B244B"),
    item_disabled=ColorPair.from_hexes("272B40", "070C25"),
    titlebar_normal=ColorPair.from_hexes("FFE0DF", "05081A"),
    titlebar_inactive=ColorPair.from_hexes("7D6B71", "05081A"),
    border_normal=AColor.from_hex("122162FF"),
    border_inactive=AColor.from_hex("282C3EFF"),
    scrollbar=Color.from_hex("070C25"),
    scrollbar_indicator_normal=Color.from_hex("0E1843"),
    scrollbar_indicator_hover=Color.from_hex("111E4F"),
    scrollbar_indicator_press=Color.from_hex("172868"),
)
"""Default color theme."""
