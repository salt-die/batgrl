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
    """
    Modifiers for input events.

    Parameters
    ----------
    alt : bool
        True if `alt` was pressed.
    ctrl : bool
        True if `ctrl` was pressed.
    shift : bool
        True if `shift` was pressed.

    Attributes
    ----------
    alt : bool
        True if `alt` was pressed.
    ctrl : bool
        True if `ctrl` was pressed.
    shift : bool
        True if `shift` was pressed.
    meta : bool
        Alias for `alt`.
    control : bool
        Alias for `ctrl`.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
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
    """
    A key press event.

    Parameters
    ----------
    key : Key | str
        The key pressed.
    mods : Mods
        Modifiers for the key.

    Attributes
    ----------
    key : Key | str
        The key pressed.
    mods : Mods
        Modifiers for the key event.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    key: Key | str
    mods: Mods

    @cache
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls, *args, **kwargs)


KeyPressEvent.ESCAPE = KeyPressEvent(Key.Escape, Mods.NO_MODS)
KeyPressEvent.ENTER = KeyPressEvent(Key.Enter, Mods.NO_MODS)


class MouseEventType(Enum):
    """
    A mouse event type.

    `MouseEventType` is one of `MOUSE_UP`, `MOUSE_DOWN`, `SCROLL_UP`,
    `SCROLL_DOWN`, `MOUSE_MOVE`.
    """
    MOUSE_UP    = "MOUSE_UP"
    MOUSE_DOWN  = "MOUSE_DOWN"
    SCROLL_UP   = "SCROLL_UP"
    SCROLL_DOWN = "SCROLL_DOWN"
    MOUSE_MOVE  = "MOUSE_MOVE"


class MouseButton(Enum):
    """
    A mouse button.

    `MouseButton` is one of `LEFT`, `MIDDLE`, `RIGHT`, `NO_BUTTON`,
    `UNKNOWN_BUTTON`.
    """
    LEFT           = "LEFT"
    MIDDLE         = "MIDDLE"
    RIGHT          = "RIGHT"
    NO_BUTTON      = "NO_BUTTON"
    UNKNOWN_BUTTON = "UNKNOWN_BUTTON"


class _PartialMouseEvent(NamedTuple):
    """
    A partial mouse input event.

    Partial mouse events are missing double-click and
    triple-click information.

    Parameters
    ----------
    position : Point
        Position of mouse.
    event_type : MouseEventType
        Mouse event type.
    button : MouseButton
        Mouse button.
    mods : Mods
        Modifiers for the mouse event.

    Attributes
    ----------
    position : Point
        Position of mouse.
    event_type : MouseEventType
        Mouse event type.
    button : MouseButton
        Mouse button.
    mods : Mods
        Modifiers for the mouse event.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    position: Point
    event_type: MouseEventType
    button: MouseButton
    mods: Mods


class MouseEvent(NamedTuple):
    """
    A mouse input event.

    Parameters
    ----------
    position : Point
        Position of mouse.
    event_type : MouseEventType
        Mouse event type.
    button : MouseButton
        Mouse button.
    mods : Mods
        Modifiers for the mouse event.
    nclicks: int
        Number of consecutive clicks. From 0 to 3 inclusive.

    Attributes
    ----------
    position : Point
        Position of mouse.
    event_type : MouseEventType
        Mouse event type.
    button : MouseButton
        Mouse button.
    mods : Mods
        Modifiers for the mouse event.
    nclicks : int
        Number of consecutive clicks. From 0 to 3 inclusive.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    position: Point
    event_type: MouseEventType
    button: MouseButton
    mods: Mods
    nclicks: int


class PasteEvent(NamedTuple):
    """
    A paste event.

    Parameters
    ----------
    paste : str
        The paste data.

    Attributes
    ----------
    paste : str
        The paste data.

    Methods
    -------
    count:
        Return number of occurrences of value.
    index:
        Return first index of value.
    """
    paste: str
