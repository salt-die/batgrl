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

from .color_types import AColor, Color, ColorPair, ColorTheme

__all__ = [
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

WHITE_ON_BLACK = ColorPair.from_colors(WHITE, BLACK)
"""White on black color pair."""

BLACK_ON_BLACK = ColorPair.from_colors(BLACK, BLACK)
"""Black on black color pair."""

DEFAULT_COLOR_THEME = ColorTheme()
"""Default color theme."""


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
