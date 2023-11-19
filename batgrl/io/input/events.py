"""Data structures for input events."""
from collections import namedtuple
from enum import Enum
from functools import cache
from typing import NamedTuple

from ...geometry import Point
from .keys import Key

__all__ = [
    "Mods",
    "Key",
    "KeyEvent",
    "MouseEventType",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
]


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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    """

    alt: bool
    ctrl: bool
    shift: bool

    @cache
    def __new__(cls, *args, **kwargs):  # noqa
        return super().__new__(cls, *args, **kwargs)

    @property
    def meta(self):
        """Alias for `alt`."""
        return self.alt

    @property
    def control(self):
        """Alias for `ctrl`."""
        return self.ctrl


Mods.NO_MODS = Mods(False, False, False)


class KeyEvent(namedtuple("KeyEvent", "key mods")):
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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    """

    key: Key | str
    mods: Mods

    @cache
    def __new__(cls, *args, **kwargs):  # noqa
        return super().__new__(cls, *args, **kwargs)


KeyEvent.CTRL_C = KeyEvent("c", Mods(False, True, False))
KeyEvent.ENTER = KeyEvent(Key.Enter, Mods.NO_MODS)
KeyEvent.ESCAPE = KeyEvent(Key.Escape, Mods.NO_MODS)


class MouseEventType(str, Enum):
    """
    A mouse event type.

    `MouseEventType` is one of `MOUSE_UP`, `MOUSE_DOWN`, `SCROLL_UP`,
    `SCROLL_DOWN`, `MOUSE_MOVE`.
    """

    MOUSE_UP = "mouse_up"
    MOUSE_DOWN = "mouse_down"
    SCROLL_UP = "scroll_up"
    SCROLL_DOWN = "scroll_down"
    MOUSE_MOVE = "mouse_move"


class MouseButton(str, Enum):
    """
    A mouse button.

    `MouseButton` is one of `LEFT`, `MIDDLE`, `RIGHT`, `NO_BUTTON`,
    `UNKNOWN_BUTTON`.
    """

    LEFT = "left"
    MIDDLE = "middle"
    RIGHT = "right"
    NO_BUTTON = "no_button"
    UNKNOWN_BUTTON = "unknown_button"


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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
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
    count(value):
        Return number of occurrences of value.
    index(value, start=0, stop=9223372036854775807):
        Return first index of value.
    """

    paste: str
