from typing import NamedTuple

from ...data_structures import Point
from .mouse_data_structures import MouseEventType, MouseButton, MouseModifier

__all__ = (
    "MouseEvent",
    "PasteEvent",
)


class MouseEvent(NamedTuple):
    position: Point
    event_type: MouseEventType
    button: MouseButton
    modifier: MouseModifier


class PasteEvent(NamedTuple):
    paste: str
