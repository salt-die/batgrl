"""Terminal Events."""

from dataclasses import dataclass
from typing import Literal

from ..colors import Color
from ..geometry import Point, Size

__all__ = [
    "ColorReportEvent",
    "CursorPositionResponseEvent",
    "DeviceAttributesReportEvent",
    "Event",
    "FocusEvent",
    "Key",
    "KeyEvent",
    "MouseEvent",
    "PasteEvent",
    "ResizeEvent",
]

# fmt: off
SpecialKey = Literal[
    "backspace", "delete", "down", "end", "enter", "escape", "f1", "f2", "f3", "f4",
    "f5", "f6", "f7", "f8", "f9", "f10", "f11", "f12", "f13", "f14", "f15", "f16",
    "f17", "f18", "f19", "f20", "f21", "f22", "f23", "f24", "home", "insert", "left",
    "page_down", "page_up", "right", "scroll_down", "scroll_up", "tab", "up",
]
"""A special keyboard key."""
CharKey = Literal[
    " ", "!", '"', "#", "$", "%", "&", "'", "(", ")", "*", "+", ",", "-", ".", "/", "0",
    "1", "2", "3", "4", "5", "6", "7", "8", "9", ":", ";", "<", "=", ">", "?", "@", "A",
    "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R",
    "S", "T", "U", "V", "W", "X", "Y", "Z", "[", "\\", "]", "^", "_", "`", "a", "b",
    "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p", "q", "r", "s",
    "t", "u", "v", "w", "x", "y", "z", "{", "|", "}", "~",
]
"""A printable character keyboard key."""
# fmt: on
Key = SpecialKey | CharKey
"""A keyboard key."""
MouseButton = Literal["left", "middle", "no_button", "right"]
"""A mouse button."""
MouseEventType = Literal[
    "mouse_down", "mouse_move", "mouse_up", "scroll_down", "scroll_up"
]
"""A mouse event type."""


class Event:
    """Base event."""


@dataclass
class UnknownEscapeSequence(Event):
    """
    Event generated from an unknown ansi escape sequence.

    Parameters
    ----------
    escape : str
        The unknown ansi escape sequence.

    Attributes
    ----------
    escape : str
        The unknown ansi escape sequence.
    """

    escape: str
    """The unknown ansi escape sequence."""


@dataclass
class ResizeEvent(Event):
    """
    A terminal resize event.

    Parameters
    ----------
    size : Size
        The new terminal size.

    Attributes
    ----------
    size : Size
        The new terminal size.
    """

    size: Size
    """The new terminal size."""


@dataclass
class CursorPositionResponseEvent(Event):
    """
    A cursor position response event.

    Parameters
    ----------
    pos : Point
        The reported cursor position.

    Attributes
    ----------
    pos : Point
        The reported cursor position.
    """

    pos: Point
    """The reported cursor position."""


@dataclass
class ColorReportEvent(Event):
    """
    A background or foreground color report event.

    Parameters
    ----------
    kind : Literal["fg", "bg"]
        Whether report is for a foreground ("fg") or background ("bg") color.
    color : Color
        The reported color.

    Attributes
    ----------
    kind : Literal["fg", "bg"]
        Whether report is for a foreground ("fg") or background ("bg") color.
    color : Color
        The reported color.
    """

    kind: Literal["fg", "bg"]
    """Whether report is for a foreground ("fg") or background ("bg") color."""
    color: Color
    """The reported color."""


@dataclass
class DeviceAttributesReportEvent(Event):
    """
    A primary device attributes report event.

    A description of the primary device attributes can be found at https://vt100.net/docs/vt510-rm/chapter4.html.
    (Search text for "Primary Device Attributes").

    Parameters
    ----------
    device_attributes : frozenset[int]
        Reported terminal attributes.

    Attributes
    ----------
    device_attributes : frozenset[int]
        Reported terminal attributes.
    """

    device_attributes: frozenset[int]
    """Reported terminal attributes."""


@dataclass
class KeyEvent(Event):
    """
    A key event.

    Parameters
    ----------
    key : Key
        The pressed key.
    alt : bool, default: False
        Whether alt was pressed.
    ctrl : bool, default: False
        Whether ctrl was pressed.
    shift : bool, default: False
        Whether shift was pressed.

    Attributes
    ----------
    key : Key
        The pressed key.
    alt : bool
        Whether alt was pressed.
    ctrl : bool
        Whether ctrl was pressed.
    shift : bool
        Whether shift was pressed.
    meta : bool
        Alias for ``alt``.
    control : bool
        Alias for ``ctrl``.
    """

    key: Key
    """The pressed key."""
    alt: bool = False
    """Whether alt was pressed."""
    ctrl: bool = False
    """Whether ctrl was pressed."""
    shift: bool = False
    """Whether shift was pressed."""

    @property
    def meta(self) -> bool:
        """Alias for ``alt``."""
        return self.alt

    @meta.setter
    def meta(self, meta: bool):
        self.alt = meta

    @property
    def control(self) -> bool:
        """Alias for ``ctrl``."""
        return self.ctrl

    @control.setter
    def control(self, control: bool):
        self.ctrl = control


@dataclass
class MouseEvent(Event):
    """
    A mouse event.

    Parameters
    ----------
    pos : Point
        The mouse position.
    button : MouseButton
        The mouse button.
    event_type : MouseEventType
        The mouse event type.
    alt : bool
        Whether alt was pressed.
    ctrl : bool
        Whether ctrl was pressed.
    shift : bool
        Whether shift was pressed.
    dy : int
        The change in y-coordinate of the mouse position.
    dx : int
        The change in x-coordinate of the mouse position.
    nclicks : int, default: 0
        The number of consecutive ``"mouse_down"`` events with same button.

    Attributes
    ----------
    pos : Point
        The mouse position.
    button : MouseButton
        The mouse button.
    event_type : MouseEventType
        The mouse event type.
    alt : bool
        Whether alt was pressed.
    ctrl : bool
        Whether ctrl was pressed.
    shift : bool
        Whether shift was pressed.
    dy : int
        The change in y-coordinate of the mouse position.
    dx : int
        The change in x-coordinate of the mouse position.
    nclicks : int
        The number of consecutive ``"mouse_down"`` events with same button.
    meta : bool
        Alias for ``alt``.
    control : bool
        Alias for ``ctrl``.
    """

    pos: Point
    """The mouse position."""
    button: MouseButton
    """The mouse button."""
    event_type: MouseEventType
    """The mouse event type."""
    alt: bool
    """Whether alt was pressed."""
    ctrl: bool
    """Whether ctrl was pressed."""
    shift: bool
    """Whether shift was pressed."""
    dy: int
    """The change in y-coordinate of the mouse position."""
    dx: int
    """The change in x-coordinate of the mouse position."""
    nclicks: int = 0
    """The number of consecutive ``"mouse_down"`` events with same button."""

    @property
    def meta(self) -> bool:
        """Alias for ``alt``."""
        return self.alt

    @meta.setter
    def meta(self, meta: bool):
        self.alt = meta

    @property
    def control(self) -> bool:
        """Alias for ``ctrl``."""
        return self.ctrl

    @control.setter
    def control(self, control: bool):
        self.ctrl = control


@dataclass
class PasteEvent(Event):
    """
    A paste event.

    Parameters
    ----------
    paste : str
        The paste content.

    Attributes
    ----------
    paste : str
        The paste content.
    """

    paste: str
    """The paste content."""


@dataclass
class FocusEvent(Event):
    """
    A focus event.

    Parameters
    ----------
    focus : Literal["in", "out"]
        The type of focus; either ``"in"`` or ``"out"``.

    Attributes
    ----------
    focus : Literal["in", "out"]
        The type of focus; either ``"in"`` or ``"out"``.
    """

    focus: Literal["in", "out"]
    """The type of focus; either ``"in"`` or ``"out"``."""
