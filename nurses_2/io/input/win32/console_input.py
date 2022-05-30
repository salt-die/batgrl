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
    # This file needs to be importable on linux for auto-documentation.
    pass
from ....data_structures import Point, Size
from ..events import (
    Key,
    Mods,
    KeyPressEvent,
    MouseButton,
    MouseEventType,
    MouseEvent,
    PasteEvent,
)
from .key_codes import KEY_CODES

RIGHT_ALT_PRESSED = 0x0001
LEFT_ALT_PRESSED = 0x0002
RIGHT_CTRL_PRESSED = 0x0004
LEFT_CTRL_PRESSED = 0x0008
SHIFT_PRESSED = 0x0010
CTRL_PRESSED = RIGHT_CTRL_PRESSED | LEFT_CTRL_PRESSED
ALT_PRESSED = RIGHT_ALT_PRESSED | LEFT_ALT_PRESSED

def _handle_key(ev: KEY_EVENT_RECORD):
    """
    Return a KeyPressEvent from a KEY_EVENT_RECORD.
    """
    key = KEY_CODES.get(ev.VirtualKeyCode, ev.uChar.UnicodeChar)

    if key == "\x00":
        return None

    key_state = ev.ControlKeyState

    alt   = bool(key_state & ALT_PRESSED)
    ctrl  = bool(key_state & CTRL_PRESSED)
    shift = bool(key_state & SHIFT_PRESSED)

    if not (isinstance(key, Key) or alt or ctrl):
        key = ev.uChar.UnicodeChar

    return KeyPressEvent(key, Mods(alt, ctrl, shift))

def _handle_mouse(ev):
    """
    Return MouseEvent from EVENT_RECORD.
    """
    FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
    RIGHTMOST_BUTTON_PRESSED =  0x0002

    MOUSE_MOVED = 0x0001
    MOUSE_WHEELED = 0x0004

    if ev.EventFlags & MOUSE_MOVED:
        event_type = MouseEventType.MOUSE_MOVE
    elif ev.EventFlags & MOUSE_WHEELED:
        if ev.ButtonState > 0:
            event_type = MouseEventType.SCROLL_UP
        else:
            event_type = MouseEventType.SCROLL_DOWN
    elif not ev.ButtonState:
        event_type = MouseEventType.MOUSE_UP
    else:
        event_type = MouseEventType.MOUSE_DOWN

    # https://docs.microsoft.com/en-us/windows/console/mouse-event-record-str?redirectedfrom=MSDN
    if not ev.ButtonState:
        button = MouseButton.NO_BUTTON
    elif ev.ButtonState & FROM_LEFT_1ST_BUTTON_PRESSED:
        button = MouseButton.LEFT
    elif ev.ButtonState & RIGHTMOST_BUTTON_PRESSED:
        button = MouseButton.RIGHT
    else:
        button = MouseButton.MIDDLE

    return MouseEvent(
        Point(ev.MousePosition.Y, ev.MousePosition.X),
        event_type,
        button,
        Mods(
            bool(ev.ControlKeyState & ALT_PRESSED),
            bool(ev.ControlKeyState & CTRL_PRESSED),
            bool(ev.ControlKeyState & SHIFT_PRESSED),
        )
    )

def _purge(text: list[str]):
    """
    Merge surrogate pairs, detect any PasteEvents and otherwise, yield Keys from text.
    Text is cleared afterwards.
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
            KeyPressEvent(
                Key.Enter if char == "\n" else char,
                Mods.NO_MODS,
            )
            for char in chars
        )

    text.clear()

def read_keys():
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
                    case KeyPressEvent.ENTER:
                        text.append("\n")
                    case KeyPressEvent(key, (alt, ctrl, _)) as key_press_event if isinstance(key, Key) or alt or ctrl:
                        yield from _purge(text)
                        yield key_press_event
                    case KeyPressEvent(char, _):
                        text.append(char)

            case MOUSE_EVENT_RECORD():
                yield from _purge(text)
                yield _handle_mouse(ev)

            case WINDOW_BUFFER_SIZE_RECORD():
                yield from _purge(text)
                yield Size(ev.Size.Y, ev.Size.X)

    yield from _purge(text)
