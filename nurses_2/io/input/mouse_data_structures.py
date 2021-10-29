from enum import Enum


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
