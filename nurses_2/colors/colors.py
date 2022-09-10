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
    primary_fg=Color.from_hex("#d1c4e9"),
    primary_bg=Color.from_hex("#311b92"),

    primary_fg_dark=Color.from_hex("#b39ddb"),
    primary_bg_dark=Color.from_hex("#29177a"),

    primary_fg_light=Color.from_hex("#ede7f6"),
    primary_bg_light=Color.from_hex("#6746c3"),

    secondary_fg=Color.from_hex("#212121"),
    secondary_bg=Color.from_hex("#ffb300"),
)
"""Default color theme."""
