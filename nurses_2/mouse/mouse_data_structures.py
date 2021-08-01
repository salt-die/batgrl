from enum import Enum, IntFlag
from typing import NamedTuple, Tuple

from ..widgets.widget_data_structures import Point

__all__ = (
    "MouseEventType",
    "MouseButton",
    "MouseModifier",
    "MouseModifierKey",
    "MouseEvent",
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


class MouseModifier(Enum):
    NO_MODIFIER       = 0
    SHIFT             = MouseModifierKey.SHIFT
    ALT               = MouseModifierKey.ALT
    SHIFT_ALT         = MouseModifierKey.SHIFT | MouseModifierKey.ALT
    CONTROL           = MouseModifierKey.CONTROL
    SHIFT_CONTROL     = MouseModifierKey.SHIFT | MouseModifierKey.CONTROL
    ALT_CONTROL       = MouseModifierKey.ALT | MouseModifierKey.CONTROL
    SHIFT_ALT_CONTROL = MouseModifierKey.SHIFT | MouseModifierKey.ALT | MouseModifierKey.CONTROL
    UNKNOWN_MODIFIER  = "UNKNOWN"


class MouseEvent(NamedTuple):
        position: Point
        event_type: MouseEventType
        button: MouseButton
        modifier: MouseModifier
