"""Data structures for input and output."""
from .input.events import _PartialMouseEvent  # noqa
from .input.events import (
    Key,
    KeyEvent,
    Mods,
    MouseButton,
    MouseEvent,
    MouseEventType,
    PasteEvent,
)

__all__ = [
    "Key",
    "Mods",
    "KeyEvent",
    "MouseEventType",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
]
