"""
Commonly used colors.
"""
from .color_data_structures import *

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
