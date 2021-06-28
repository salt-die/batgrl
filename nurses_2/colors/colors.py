"""
Commonly used colors.
"""
from .color_types import *

WHITE = RGB(255, 255, 255)
BLACK = RGB(0, 0, 0)
RED = RGB(255, 0, 0)
GREEN = RGB(0, 255, 0)
BLUE= RGB(0, 0, 255)
YELLOW = RGB(255, 255, 0)
CYAN = RGB(0, 255, 255)
MAGENTA = RGB(255, 0, 255)

WHITE_ON_BLACK = ColorPair(*WHITE, *BLACK)
