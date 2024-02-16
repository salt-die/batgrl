from batgrl.colors import AWHITE, AColor, lerp_colors

RED = AColor.from_hex("cc2808")  # Front
ORANGE = AColor.from_hex("f46e07")  # Back
GREEN = AColor.from_hex("3edd08")  # Top
BLUE = AColor.from_hex("083add")  # Bottom
YELLOW = AColor.from_hex("e8ef13")  # Left
WHITE = AColor.from_hex("efefe8")  # Right

FACE_COLORS = RED, ORANGE, GREEN, BLUE, YELLOW, WHITE
SELECTED_COLORS = tuple(lerp_colors(color, AWHITE, 0.5) for color in FACE_COLORS)
