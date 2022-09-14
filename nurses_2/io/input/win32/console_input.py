"""
Parse and create events for each input record from a win32 console.
"""
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

# Last mouse button pressed is needed to get behavior
# consistent with linux mouse handling.
_PRESSED_KEYS = [0]
_INT_TO_KEYS = {
    # FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    # RIGHTMOST_BUTTON_PRESSED = 0x0002
    # FROM_LEFT_2ND_BUTTON_PRESSED = 0x0004
    0: MouseButton.NO_BUTTON,
    1: MouseButton.LEFT,
    2: MouseButton.RIGHT,
    4: MouseButton.MIDDLE,
}

def _handle_mods(key_state: DWORD) -> Mods:
    """
    Return `Mods` from an event's `ControlKeyState`.
    """
    ALT_PRESSED = 0x0001 | 0x0002  # left alt or right alt
    CTRL_PRESSED = 0x0004 | 0x0008  # left ctrl or right ctrl
    SHIFT_PRESSED = 0x0010

    alt   = bool(key_state & ALT_PRESSED)
    ctrl  = bool(key_state & CTRL_PRESSED)
    shift = bool(key_state & SHIFT_PRESSED)
    return Mods(alt, ctrl, shift)

def _handle_key(ev: KEY_EVENT_RECORD) -> KeyEvent:
    """
    Return a `KeyEvent` from a `KEY_EVENT_RECORD`.
    """
    key = KEY_CODES.get(ev.VirtualKeyCode, ev.uChar.UnicodeChar)

    if key == "\x00":
        return None

    mods = _handle_mods(ev.ControlKeyState)

    if not (isinstance(key, Key) or mods.alt or mods.ctrl):
        key = ev.uChar.UnicodeChar

    return KeyEvent(key, mods)

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
        button_state = _PRESSED_KEYS[-1]  # Last button pressed.
    elif ev.EventFlags & MOUSE_WHEELED:
        if ev.ButtonState > 0:
            event_type = MouseEventType.SCROLL_UP
        else:
            event_type = MouseEventType.SCROLL_DOWN
        button_state = 4  # Middle mouse button.
    elif ev.ButtonState < last_button_state:
        event_type = MouseEventType.MOUSE_UP
        _PRESSED_KEYS.remove(button_state := last_button_state - ev.ButtonState)
    else:
        event_type = MouseEventType.MOUSE_DOWN
        _PRESSED_KEYS.append(button_state := ev.ButtonState - last_button_state)

    return _PartialMouseEvent(
        Point(ev.MousePosition.Y, ev.MousePosition.X),
        event_type,
        _INT_TO_KEYS[button_state],
        _handle_mods(ev.ControlKeyState),
    )

def _purge(text: list[str]):
    """
    Merge surrogate pairs, detect any PasteEvents and otherwise, yield Keys from `text`.
    `text` is cleared afterwards.
    """
    if not text:
        return

    chars = (
        "".join(text)
        .encode("utf-16", "surrogatepass")
        .decode("utf-16")
    )  # Merge surrogate pairs.

    if len(chars) > 2 or not chars.isascii():  # Heuristic for detecting paste event.
        yield PasteEvent(chars)

    else:
        yield from (
            KeyEvent(
                Key.Enter if char == "\n" else char,
                Mods.NO_MODS,
            )
            for char in chars
        )

    text.clear()

def events():
    """
    Yield input events.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
    """
    input_records = (INPUT_RECORD * 1024)()

    windll.kernel32.ReadConsoleInputW(
        STD_INPUT_HANDLE, input_records, 1024, byref(DWORD(0))
    )

    text = [ ]
    for ir in input_records:
        match ev := getattr(ir.Event, EventTypes.get(ir.EventType, ""), None):
            case KEY_EVENT_RECORD() if ev.KeyDown:
                match _handle_key(ev):
                    case None:
                        continue
                    case KeyEvent.ENTER:
                        text.append("\n")
                    case KeyEvent(key, (alt, ctrl, _)) as key_event if isinstance(key, Key) or alt or ctrl:
                        yield from _purge(text)
                        yield key_event
                    case KeyEvent(char, _):
                        text.append(char)

            case MOUSE_EVENT_RECORD():
                yield from _purge(text)
                yield _handle_mouse(ev)

            case WINDOW_BUFFER_SIZE_RECORD():
                yield from _purge(text)
                yield Size(ev.Size.Y, ev.Size.X)

    yield from _purge(text)
