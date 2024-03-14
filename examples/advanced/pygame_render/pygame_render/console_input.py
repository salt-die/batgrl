from collections import OrderedDict
from collections.abc import Iterator

import pygame as pg
from batgrl.geometry import Point, Size
from batgrl.io import (
    Key,
    KeyEvent,
    Mods,
    MouseButton,
    MouseEventType,
    PasteEvent,
    _PartialMouseEvent,
)

from . import FONT_HEIGHT, FONT_WIDTH

_PYGAME_BUTTONS = {
    -1: MouseButton.NO_BUTTON,
    1: MouseButton.LEFT,
    2: MouseButton.MIDDLE,
    3: MouseButton.RIGHT,
}
_PRESSED_BUTTONS = OrderedDict.fromkeys([-1])

_MODS = dict.fromkeys(["lalt", "lctrl", "lshift", "ralt", "rctrl", "rshift"], False)
_PYGAME_MODS = {
    pg.K_LALT: "lalt",
    pg.K_LCTRL: "lctrl",
    pg.K_LSHIFT: "lshift",
    pg.K_RALT: "ralt",
    pg.K_RCTRL: "rctrl",
    pg.K_RSHIFT: "rshift",
}
_PYGAME_KEYS = {
    pg.K_ESCAPE: Key.Escape,
    pg.K_LEFT: Key.Left,
    pg.K_RIGHT: Key.Right,
    pg.K_UP: Key.Up,
    pg.K_DOWN: Key.Down,
    pg.K_HOME: Key.Home,
    pg.K_END: Key.End,
    pg.K_INSERT: Key.Insert,
    pg.K_DELETE: Key.Delete,
    pg.K_PAGEUP: Key.PageUp,
    pg.K_PAGEDOWN: Key.PageDown,
    pg.K_F1: Key.F1,
    pg.K_F2: Key.F2,
    pg.K_F3: Key.F3,
    pg.K_F4: Key.F4,
    pg.K_F5: Key.F5,
    pg.K_F6: Key.F6,
    pg.K_F7: Key.F7,
    pg.K_F8: Key.F8,
    pg.K_F9: Key.F9,
    pg.K_F10: Key.F10,
    pg.K_F11: Key.F11,
    pg.K_F12: Key.F12,
    pg.K_F13: Key.F13,
    pg.K_F14: Key.F14,
    pg.K_F15: Key.F15,
    pg.K_TAB: Key.Tab,
    pg.K_RETURN: Key.Enter,
    pg.K_BACKSPACE: Key.Backspace,
}
_ESCAPES = {
    "\x01": "a",
    "\x02": "b",
    "\x03": "c",
    "\x04": "d",
    "\x05": "e",
    "\x06": "f",
    "\x07": "g",
    "\x0b": "k",
    "\x0c": "l",
    "\x0e": "n",
    "\x0f": "o",
    "\x10": "p",
    "\x11": "q",
    "\x12": "r",
    "\x13": "s",
    "\x14": "t",
    "\x15": "u",
    "\x16": "v",
    "\x17": "w",
    "\x18": "x",
    "\x19": "y",
    "\x1a": "z",
    "\x1b": "3",
    "\x1c": "4",
    "\x1d": "5",
    "\x1e": "6",
    "\x1f": "7",
    "\x7f": "8",
}


def _get_mods(shift: bool = True) -> Mods:
    return Mods(
        _MODS["lalt"] or _MODS["ralt"],
        _MODS["lctrl"] or _MODS["rctrl"],
        shift and (_MODS["lshift"] or _MODS["rshift"]),
    )


def _handle_mods(event: pg.event.Event) -> None:
    _MODS[_PYGAME_MODS[event.key]] = event.type == pg.KEYDOWN


def _handle_key(event: pg.event.Event) -> KeyEvent | PasteEvent | None:
    """Return a `KeyEvent` from a pygame event."""
    if key := _PYGAME_KEYS.get(event.key):
        return KeyEvent(key, _get_mods())

    if event.key in _PYGAME_MODS:
        return _handle_mods(event)

    if key := _ESCAPES.get(event.unicode):
        mods = _get_mods()
        if key == "v" and mods == Mods(False, True, False):
            return PasteEvent((pg.scrap.get(pg.SCRAP_TEXT) or b"").decode())
        else:
            return KeyEvent(key, mods)

    if event.unicode.isascii():
        return KeyEvent(event.unicode, _get_mods(shift=False))


def _handle_mouse(event: pg.event.Event) -> _PartialMouseEvent:
    """Return `_PartialMouseEvent` from a pygame event."""
    if event.type == pg.MOUSEMOTION:
        event_type = MouseEventType.MOUSE_MOVE
        button_state = next(reversed(_PRESSED_BUTTONS))
    elif event.type == pg.MOUSEWHEEL:
        if event.y > 0:
            event_type = MouseEventType.SCROLL_UP
        else:
            event_type = MouseEventType.SCROLL_DOWN
        button_state = 2
    elif event.type == pg.MOUSEBUTTONUP:
        event_type = MouseEventType.MOUSE_UP
        button_state = 2
        _PRESSED_BUTTONS.pop(button_state, None)
    else:
        event_type = MouseEventType.MOUSE_DOWN
        button_state = event.button
        _PRESSED_BUTTONS[button_state] = None
        _PRESSED_BUTTONS.move_to_end(button_state)

    x, y = pg.mouse.get_pos()
    return _PartialMouseEvent(
        Point(y // FONT_HEIGHT, x // FONT_WIDTH),
        event_type,
        _PYGAME_BUTTONS[button_state],
        _get_mods(),
    )


def events() -> Iterator[KeyEvent | PasteEvent | Size | _PartialMouseEvent]:
    """Yield input events."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            yield KeyEvent.CTRL_C
        elif (
            (event.type == pg.MOUSEBUTTONDOWN or event.type == pg.MOUSEBUTTONUP)
            and event.button <= 3
            or event.type == pg.MOUSEMOTION
            or event.type == pg.MOUSEWHEEL
        ):
            yield _handle_mouse(event)
        elif event.type == pg.KEYDOWN:
            if key := _handle_key(event):
                yield key
        elif event.type == pg.KEYUP and event.key in _PYGAME_MODS:
            _handle_mods(event)
        elif event.type == pg.VIDEORESIZE:
            yield Size(event.h // FONT_HEIGHT, event.w // FONT_WIDTH)
