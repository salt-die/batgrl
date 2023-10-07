from batgrl.colors import BLACK, GREEN, WHITE, ColorPair, lerp_colors

MORE_BRIGHT_GREEN = lerp_colors(GREEN, WHITE, 0.70)
BRIGHT_GREEN = lerp_colors(GREEN, WHITE, 0.30)
DARK_GREEN = lerp_colors(GREEN, BLACK, 0.96)
LESS_DARK_GREEN = lerp_colors(GREEN, BLACK, 0.92)
BRIGHT_COLOR_PAIR = ColorPair.from_colors(MORE_BRIGHT_GREEN, LESS_DARK_GREEN)
DEFAULT_COLOR_PAIR = ColorPair.from_colors(BRIGHT_GREEN, DARK_GREEN)
