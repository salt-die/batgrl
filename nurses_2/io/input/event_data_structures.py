from functools import cache
from collections import namedtuple
from typing import NamedTuple

from ...data_structures import Point
from .keys import Key
from .mouse_data_structures import MouseEventType, MouseButton

__all__ = (
    "Mods",
    "KeyPressEvent",
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


class KeyPressEvent(namedtuple("KeyPressEvent", "key modifiers")):
    key: Key | str
    modifiers: Mods

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)

    @property
    def mods(self):
        return self.modifiers


class MouseEvent(NamedTuple):
    position: Point
    event_type: MouseEventType
    button: MouseButton
    modifier: Mods


class PasteEvent(NamedTuple):
    paste: str
