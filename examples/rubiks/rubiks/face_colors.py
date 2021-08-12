from nurses_2.colors import RED, YELLOW, WHITE, GREEN, BLUE, Color

FRONT_COLOR  = RED
BACK_COLOR   = ORANGE = Color.from_hex("f46e07")
TOP_COLOR    = GREEN
BOTTOM_COLOR = BLUE
LEFT_COLOR   = YELLOW
RIGHT_COLOR  = WHITE

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
        *(127 + channel // 2 for channel in color)
    )
    for color in FACE_COLORS
)