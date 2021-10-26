from typing import NamedTuple

from ...data_structures import Point
from .keys import Key
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


# TODO: KeyPressEvents.  Currently, for most keypresses we send single characters to `on_press` methods.
# TODO: Move following Modifier into MouseEvent as well.
# For alt-presses, a single character will be preceded by Key.Escape. This complicates binding alt-presses.
# Instead, we can package everything into a KeyPressEvent.
class Modifiers(NamedTuple):
    shift: bool
    alt: bool
    ctrl: bool


class KeyPressEvent(NamedTuple):
    key: Key | str
    modifiers: Modifiers
