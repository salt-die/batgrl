"""Parse and create events for each input record from a win32 console."""
from collections import OrderedDict
from collections.abc import Iterable
from ctypes import byref, windll
from ctypes.wintypes import DWORD

from ....geometry import Point, Size
from ...win32_types import (
    INPUT_RECORD,
    KEY_EVENT_RECORD,
    MOUSE_EVENT_RECORD,
    STD_INPUT_HANDLE,
    WINDOW_BUFFER_SIZE_RECORD,
)
from ..events import (
    Key,
    KeyEvent,
    Mods,
    MouseButton,
    MouseEventType,
    PasteEvent,
    _PartialMouseEvent,
)
from .key_codes import KEY_CODES

_EVENT_TYPES = {1: "KeyEvent", 2: "MouseEvent", 4: "WindowBufferSizeEvent"}
_INT_TO_KEYS = {
    0: MouseButton.NO_BUTTON,
    1: MouseButton.LEFT,
    2: MouseButton.RIGHT,
    4: MouseButton.MIDDLE,
}
# Last mouse button pressed is needed to get behavior consistent with linux mouse
# handling. OrderedDict is being used as an ordered-set.
_PRESSED_BUTTONS = OrderedDict.fromkeys([0])
_TEXT: list[str] = []


def _handle_mods(key_state: DWORD) -> Mods:
    """Return `Mods` from an event's `ControlKeyState`."""
    # Magic numbers are:
    # LEFT_ALT | RIGHT_ALT => 0x0001 | 0x0002 => 0x0003
    # LEFT_CTRL | RIGHT_CTRL => 0x0004 | 0x0008 => 0x000C
    # SHIFT is 0x0010
    alt = bool(key_state & 0x0003)
    ctrl = bool(key_state & 0x000C)
    shift = bool(key_state & 0x0010)
    return Mods(alt, ctrl, shift)


def _handle_key(ev: KEY_EVENT_RECORD) -> KeyEvent | None:
    """Return a `KeyEvent` or add a character to _TEXT from a `KEY_EVENT_RECORD`."""
    key = KEY_CODES.get(ev.VirtualKeyCode, ev.uChar.UnicodeChar)
    if key == "\x00":
        return

    mods = _handle_mods(ev.ControlKeyState)

    if key is Key.Enter and not any(mods):
        _TEXT.append("\n")
    elif mods.alt or mods.ctrl or isinstance(key, Key):
        return KeyEvent(key, mods)
    else:
        _TEXT.append(ev.uChar.UnicodeChar)


def _handle_mouse(ev: MOUSE_EVENT_RECORD) -> _PartialMouseEvent:
    """
    Return `_PartialMouseEvent` from `EVENT_RECORD`.

    Reference: https://docs.microsoft.com/en-us/windows/console/mouse-event-record-str
    """
    last_button_state = sum(_PRESSED_BUTTONS)

    # On linux, for simultaneous button presses, only the most recent button pressed or
    # released is given. On windows, simultaneous mouse button presses are communicated
    # through ev.ButtonState. To get behavior roughly consistent with linux, the most
    # recent mouse button pressed is determined from the last button state, the current
    # button state, and the order mouse buttons were pressed (stored in
    # _PRESSED_BUTTONS).

    # Double-click can be determined from ev.EventFlags (0x0002), but to be consistent
    # with linux mouse-handling we determine double/triple-clicks with
    # `batgrl.app.App`.
    if ev.EventFlags & 0x0001:  # 0x0001 is mouse moved flag
        event_type = MouseEventType.MOUSE_MOVE
        button_state = next(reversed(_PRESSED_BUTTONS))  # Last button pressed.
    elif ev.EventFlags & 0x0004:  # 0x0004 is mouse wheeled flag
        if ev.ButtonState > 0:
            event_type = MouseEventType.SCROLL_UP
        else:
            event_type = MouseEventType.SCROLL_DOWN
        button_state = 4  # Middle mouse button.
    elif ev.ButtonState < last_button_state:
        event_type = MouseEventType.MOUSE_UP
        button_state = last_button_state - ev.ButtonState
        _PRESSED_BUTTONS.pop(button_state, None)
    else:
        event_type = MouseEventType.MOUSE_DOWN
        button_state = ev.ButtonState - last_button_state
        _PRESSED_BUTTONS[button_state] = None
        _PRESSED_BUTTONS.move_to_end(button_state)

    return _PartialMouseEvent(
        Point(ev.MousePosition.Y, ev.MousePosition.X),
        event_type,
        _INT_TO_KEYS.get(button_state, MouseButton.NO_BUTTON),
        _handle_mods(ev.ControlKeyState),
    )


def _purge_text() -> Iterable[PasteEvent | KeyEvent]:
    """
    While generating events, key events are collected into _TEXT to determine if a paste
    event has occurred. If there many key events or there are non-ascii character keys,
    this function yields a single PasteEvent. Otherwise yields KeyEvents from _TEXT.
    _TEXT is cleared afterwards.
    """
    if len(_TEXT) == 0:
        return

    chars = (
        "".join(_TEXT).encode("utf-16", "surrogatepass").decode("utf-16")
    )  # Merge surrogate pairs.
    _TEXT.clear()

    if len(chars) > 2 or not chars.isascii():  # Heuristic for detecting paste event.
        yield PasteEvent(chars)
    else:
        for char in chars:
            yield KeyEvent(Key.Enter if char == "\n" else char, Mods.NO_MODS)


def events() -> Iterable[KeyEvent | PasteEvent | Size | _PartialMouseEvent]:
    """
    Yield input events.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
    """
    input_records = (INPUT_RECORD * 1024)()

    windll.kernel32.ReadConsoleInputW(
        STD_INPUT_HANDLE, input_records, 1024, byref(DWORD(0))
    )

    for ir in input_records:
        if ir.EventType not in _EVENT_TYPES:
            continue

        ev = getattr(ir.Event, _EVENT_TYPES[ir.EventType])

        if isinstance(ev, KEY_EVENT_RECORD):
            if ev.KeyDown and (key := _handle_key(ev)):
                yield from _purge_text()
                yield key
        elif isinstance(ev, MOUSE_EVENT_RECORD):
            yield from _purge_text()
            yield _handle_mouse(ev)
        elif isinstance(ev, WINDOW_BUFFER_SIZE_RECORD):
            yield from _purge_text()
            yield Size(ev.Size.Y, ev.Size.X)

    yield from _purge_text()
