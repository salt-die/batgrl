from nurses_2.colors import Color, ColorPair

ZERO = Color.from_hex("aba1ad")
ONE = Color.from_hex("272ae5")
TWO = Color.from_hex("25ba0b")
THREE = Color.from_hex("8e2222")
FOUR = Color.from_hex("0a2b99")
FIVE = Color.from_hex("7f1b07")
SIX = Color.from_hex("0ba9c1")
SEVEN = Color.from_hex("c013db")
EIGHT = Color.from_hex("140116")

BORDER = Color.from_hex("85698c")

HIDDEN_SQUARE = Color.from_hex("56365e")
HIDDEN = ColorPair.from_colors(HIDDEN_SQUARE, BORDER)
HIDDEN_REVERSED = ColorPair.from_colors(BORDER, HIDDEN_SQUARE)

COUNT_SQUARE = Color.from_hex("b0d9e5")
COUNT = ColorPair.from_colors(BORDER, COUNT_SQUARE)

DATA_BAR = ColorPair.from_colors(HIDDEN_SQUARE, COUNT_SQUARE)

FLAG_COLOR = Color.from_hex("6d1004")
