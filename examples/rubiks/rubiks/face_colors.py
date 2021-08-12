from nurses_2.colors import Color

FRONT_COLOR  = RED = Color.from_hex("cc2808")
BACK_COLOR   = ORANGE = Color.from_hex("f46e07")
TOP_COLOR    = GREEN = Color.from_hex("3edd08")
BOTTOM_COLOR = BLUE = Color.from_hex("083add")
LEFT_COLOR   = YELLOW = Color.from_hex("e8ef13")
RIGHT_COLOR  = WHITE = Color.from_hex("efefe8")

FACE_COLORS = (
    FRONT_COLOR,
    BACK_COLOR,
    TOP_COLOR,
    BOTTOM_COLOR,
    LEFT_COLOR,
    RIGHT_COLOR,
)

SELECTED_COLORS = tuple(
    Color(
        *(85 + 2 * channel // 3 for channel in color)
    )
    for color in FACE_COLORS
)