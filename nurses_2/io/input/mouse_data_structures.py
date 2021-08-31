from enum import Enum, IntFlag

__all__ = (
    "MouseEventType",
    "MouseButton",
    "MouseModifier",
    "MouseModifierKey",
)


class MouseEventType(Enum):
    MOUSE_UP    = "MOUSE_UP"
    MOUSE_DOWN  = "MOUSE_DOWN"
    SCROLL_UP   = "SCROLL_UP"
    SCROLL_DOWN = "SCROLL_DOWN"
    MOUSE_MOVE  = "MOUSE_MOVE"


class MouseButton(Enum):
    LEFT           = "LEFT"
    MIDDLE         = "MIDDLE"
    RIGHT          = "RIGHT"
    NO_BUTTON      = "NO_BUTTON"
    UNKNOWN_BUTTON = "UNKNOWN_BUTTON"


class MouseModifierKey(IntFlag):
    SHIFT   = 1
    ALT     = 2
    CONTROL = 4


SHIFT = MouseModifierKey.SHIFT
ALT = MouseModifierKey.ALT
CONTROL = MouseModifierKey.CONTROL


class MouseModifier(Enum):
    NO_MODIFIER       = 0
    SHIFT             = SHIFT
    ALT               = ALT
    SHIFT_ALT         = SHIFT | ALT
    CONTROL           = CONTROL
    SHIFT_CONTROL     = SHIFT | CONTROL
    ALT_CONTROL       = ALT | CONTROL
    SHIFT_ALT_CONTROL = SHIFT | ALT | CONTROL
    UNKNOWN_MODIFIER  = "UNKNOWN"
