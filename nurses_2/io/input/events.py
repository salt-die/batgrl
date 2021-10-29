from functools import cache
from collections import namedtuple
from enum import Enum
from typing import NamedTuple

from ...data_structures import Point
from .keys import Key

__all__ = (
    "Mods",
    "Key",
    "KeyPressEvent",
    "MouseEventType",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
)


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


Mods.NO_MODS = Mods(False, False, False)


class KeyPressEvent(namedtuple("KeyPressEvent", "key mods")):
    key: Key | str
    mods: Mods

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


KeyPressEvent.ESCAPE = KeyPressEvent(Key.Escape, Mods.NO_MODS)
KeyPressEvent.ENTER = KeyPressEvent(Key.Enter, Mods.NO_MODS)


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


class MouseEvent(NamedTuple):
    position: Point
    event_type: MouseEventType
    button: MouseButton
    mods: Mods


class PasteEvent(NamedTuple):
    paste: str
