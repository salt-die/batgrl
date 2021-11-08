from nurses_2.colors import AColor

from_hex = AColor.from_hex

RED    = from_hex("cc2808")  # Front
ORANGE = from_hex("f46e07")  # Back
GREEN  = from_hex("3edd08")  # Top
BLUE   = from_hex("083add")  # Bottom
YELLOW = from_hex("e8ef13")  # Left
WHITE  = from_hex("efefe8")  # Right

FACE_COLORS = (
    RED,
    ORANGE,
    GREEN,
    BLUE,
    YELLOW,
    WHITE,
)

# Brighten FACE_COLORS
SELECTED_COLORS = tuple(
    AColor(
        *(85 + 2 * channel // 3 for channel in color[:3])
    )
    for color in FACE_COLORS
)
