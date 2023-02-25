from nurses_2.colors import BLACK, GREEN, WHITE, lerp_colors, ColorPair

MORE_BRIGHT_GREEN = lerp_colors(GREEN, WHITE, .70)
BRIGHT_GREEN = lerp_colors(GREEN, WHITE, .30)
DARK_GREEN = lerp_colors(GREEN, BLACK, .96)
LESS_DARK_GREEN = lerp_colors(GREEN, BLACK, .92)
BRIGHT_COLOR_PAIR = ColorPair.from_colors(MORE_BRIGHT_GREEN, LESS_DARK_GREEN)
DEFAULT_COLOR_PAIR = ColorPair.from_colors(BRIGHT_GREEN, DARK_GREEN)
