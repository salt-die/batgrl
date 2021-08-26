from nurses_2.colors import Color, color_pair

from_hex = Color.from_hex

ZERO            = from_hex("aba1ad")
ONE             = from_hex("272ae5")
TWO             = from_hex("2ae527")
THREE           = from_hex("e53327")
FOUR            = from_hex("0a2b99")
FIVE            = from_hex("7f1b07")
SIX             = from_hex("0ba9c1")
SEVEN           = from_hex("c013db")
EIGHT           = from_hex("140116")

BORDER          = from_hex("85698c")

HIDDEN_SQUARE   = from_hex("56365e")
HIDDEN          = color_pair(HIDDEN_SQUARE, BORDER)
HIDDEN_REVERSED = color_pair(BORDER, HIDDEN_SQUARE)

COUNT_SQUARE    = from_hex("b0d9e5")
COUNT           = color_pair(BORDER, COUNT_SQUARE)
