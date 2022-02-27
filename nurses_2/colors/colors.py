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

WHITE   = Color(255, 255, 255)
BLACK   = Color(  0,   0,   0)
RED     = Color(255,   0,   0)
GREEN   = Color(  0, 255,   0)
BLUE    = Color(  0,   0, 255)
YELLOW  = Color(255, 255,   0)
CYAN    = Color(  0, 255, 255)
MAGENTA = Color(255,   0, 255)

AWHITE   = AColor(255, 255, 255)
ABLACK   = AColor(  0,   0,   0)
ARED     = AColor(255,   0,   0)
AGREEN   = AColor(  0, 255,   0)
ABLUE    = AColor(  0,   0, 255)
AYELLOW  = AColor(255, 255,   0)
ACYAN    = AColor(  0, 255, 255)
AMAGENTA = AColor(255,   0, 255)
TRANSPARENT = AColor(0, 0, 0, 0)

WHITE_ON_BLACK = ColorPair.from_colors(WHITE, BLACK)
BLACK_ON_BLACK = ColorPair.from_colors(BLACK, BLACK)

DEFAULT_COLOR_THEME = ColorTheme(
    primary_fg=Color.from_hex("#d1c4e9"),
    primary_bg=Color.from_hex("#311b92"),

    primary_fg_dark=Color.from_hex("#b39ddb"),
    primary_bg_dark=Color.from_hex("#000063"),

    primary_fg_light=Color.from_hex("#ede7f6"),
    primary_bg_light=Color.from_hex("#6746c3"),

    secondary_fg=Color.from_hex("#212121"),
    secondary_bg=Color.from_hex("#ffb300"),
)