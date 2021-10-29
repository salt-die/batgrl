from functools import cache
from collections import namedtuple
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
# collections.namedtuple used so __new__ can be cached.
class Mods(namedtuple("Mods", "alt ctrl shift")):
    alt: bool
    ctrl: bool
    shift: bool

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    @property
    def meta(self):
        """
        Alias for `alt`.
        """
        return self.alt

    @property
    def control(self):
        """
        Alias for `ctrl`.
        """
        return self.ctrl


class KeyPressEvent(namedtuple("KeyPressEvent", "key modifiers")):
    key: Key | str
    modifiers: Mods

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    @property
    def mods(self):
        return self.modifiers
