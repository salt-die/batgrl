"""
Parse and create events for each input record from a win32 console.
"""
from collections import OrderedDict

try:
    from ctypes.wintypes import DWORD
    from ctypes import byref, windll
    from ...win32_types import (
        INPUT_RECORD,
        KEY_EVENT_RECORD,
        MOUSE_EVENT_RECORD,
        STD_INPUT_HANDLE,
        WINDOW_BUFFER_SIZE_RECORD,
        EventTypes,
    )
except ModuleNotFoundError:
    # Assign arbitrary types so file is importable on linux for auto-documentation.
    DWORD = type(None)
    KEY_EVENT_RECORD = type(None)
    MOUSE_EVENT_RECORD = type(None)

from ....data_structures import Point, Size
from ..events import (
    Key,
    Mods,
    KeyEvent,
    MouseButton,
    MouseEventType,
    _PartialMouseEvent,
    PasteEvent,
)
from .key_codes import KEY_CODES

_INT_TO_KEYS = {
    # FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    # RIGHTMOST_BUTTON_PRESSED = 0x0002
    # FROM_LEFT_2ND_BUTTON_PRESSED = 0x0004
    0: MouseButton.NO_BUTTON,
    1: MouseButton.LEFT,
    2: MouseButton.RIGHT,
    4: MouseButton.MIDDLE,
}
# Last mouse button pressed is needed to get behavior consistent with linux mouse handling.
# OrderedDict is being used as an ordered-set.
_PRESSED_KEYS = OrderedDict.fromkeys([0])
_TEXT: list[str] = []

def _handle_mods(key_state: DWORD) -> Mods:
    """
    Return `Mods` from an event's `ControlKeyState`.
    """
    ALT_PRESSED = 0x0001 | 0x0002  # left alt or right alt
    CTRL_PRESSED = 0x0004 | 0x0008  # left ctrl or right ctrl
    SHIFT_PRESSED = 0x0010

    alt = bool(key_state & ALT_PRESSED)
    ctrl = bool(key_state & CTRL_PRESSED)
    shift = bool(key_state & SHIFT_PRESSED)
    return Mods(alt, ctrl, shift)

def _handle_key(ev: KEY_EVENT_RECORD) -> KeyEvent:
    """
    Return a `KeyEvent` or add a character to _TEXT from a `KEY_EVENT_RECORD`.
    """
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
    MOUSE_MOVED = 0x0001
    MOUSE_WHEELED = 0x0004
    last_button_state = sum(_PRESSED_KEYS)

    # On windows, simultaneous mouse button presses are communicated through ev.ButtonState.
    # Linux only passes the last button pressed through ansi codes. To get behavior consistent with
    # linux, the last mouse button pressed is determined from the last button state, the current
    # button state, and the order mouse buttons were pressed (stored in _PRESSED_KEYS).

    # Double-click can be determined from ev.EventFlags (0x0002), but to be consistent with
    # linux mouse-handling we determine double/triple-clicks with `nurses_2.app.App`.
    if ev.EventFlags & MOUSE_MOVED:
        event_type = MouseEventType.MOUSE_MOVE
        button_state = next(reversed(_PRESSED_KEYS))  # Last button pressed.
    elif ev.EventFlags & MOUSE_WHEELED:
        if ev.ButtonState > 0:
            event_type = MouseEventType.SCROLL_UP
        else:
            event_type = MouseEventType.SCROLL_DOWN
        button_state = 4  # Middle mouse button.
    elif ev.ButtonState < last_button_state:
        event_type = MouseEventType.MOUSE_UP
        button_state = last_button_state - ev.ButtonState
        _PRESSED_KEYS.pop(button_state, None)
    else:
        event_type = MouseEventType.MOUSE_DOWN
        button_state = ev.ButtonState - last_button_state
        _PRESSED_KEYS[button_state] = None
        _PRESSED_KEYS.move_to_end(button_state)

    return _PartialMouseEvent(
        Point(ev.MousePosition.Y, ev.MousePosition.X),
        event_type,
        _INT_TO_KEYS.get(button_state, MouseButton.NO_BUTTON),
        _handle_mods(ev.ControlKeyState),
    )

def _purge_text():
    """
    Key events are first collected into _TEXT to determine if a paste event has occurred.
    """
    if not _TEXT:
        return

    chars = "".join(_TEXT).encode("utf-16", "surrogatepass").decode("utf-16")  # Merge surrogate pairs.
    _TEXT.clear()

    if len(chars) > 2 or not chars.isascii():  # Heuristic for detecting paste event.
        yield PasteEvent(chars)
    else:
        for char in chars:
            yield KeyEvent(Key.Enter if char == "\n" else char, Mods.NO_MODS)

def events():
    """
    Yield input events.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
    """
    input_records = (INPUT_RECORD * 1024)()

    windll.kernel32.ReadConsoleInputW(
        STD_INPUT_HANDLE, input_records, 1024, byref(DWORD(0))
    )

    for ir in input_records:
        match ev := getattr(ir.Event, EventTypes.get(ir.EventType, ""), None):
            case KEY_EVENT_RECORD() if ev.KeyDown:
                if (key := _handle_key(ev)) is not None:
                    yield from _purge_text()
                    yield key

            case MOUSE_EVENT_RECORD():
                yield from _purge_text()
                yield _handle_mouse(ev)

            case WINDOW_BUFFER_SIZE_RECORD():
                yield from _purge_text()
                yield Size(ev.Size.Y, ev.Size.X)

    yield from _purge_text()
