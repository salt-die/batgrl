"""
Parse and create events for each input record from a win32 console.
"""
from ctypes.wintypes import DWORD, HANDLE
from ctypes import pointer, windll

from ....data_structures import Point
from ...win32_types import (
    INPUT_RECORD,
    KEY_EVENT_RECORD,
    MOUSE_EVENT_RECORD,
    STD_INPUT_HANDLE,
    EventTypes,
)
from ..keys import Key
from ..events import Mods, KeyPressEvent, MouseButton, MouseEventType, MouseEvent, PasteEvent
from .key_maps import ANSI_SEQUENCES, KEY_CODES

RIGHT_ALT_PRESSED = 0x0001
LEFT_ALT_PRESSED = 0x0002
RIGHT_CTRL_PRESSED = 0x0004
LEFT_CTRL_PRESSED = 0x0008
SHIFT_PRESSED = 0x0010
CTRL_PRESSED = RIGHT_CTRL_PRESSED | LEFT_CTRL_PRESSED
ALT_PRESSED = RIGHT_ALT_PRESSED | LEFT_ALT_PRESSED

STDIN_HANDLE = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

def _handle_key(ev: KEY_EVENT_RECORD):
    """
    Return a KeyPressEvent from a KEY_EVENT_RECORD.
    """
    match ev.uChar.UnicodeChar:
        case "\x00":
            key = KEY_CODES.get(ev.VirtualKeyCode)

            if key is None:
                return

        case u_char:
            key = ANSI_SEQUENCES.get(u_char.encode(errors="surrogatepass"), u_char)

    return KeyPressEvent(
        key,
        Mods(
            bool(ev.ControlKeyState & ALT_PRESSED),
            bool(ev.ControlKeyState & CTRL_PRESSED),
            bool(ev.ControlKeyState & SHIFT_PRESSED),
        )
    )

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
    chars = (
        "".join(text)
        .encode("utf-16", "surrogatepass")
        .decode("utf-16")
    )  # Merge surrogate pairs.

    if "\n" in chars and len(chars) > 3:  # Heuristic for detecting paste event.
        yield PasteEvent(chars)

    else:
        yield from (
            KeyPressEvent(
                Key.Enter if char == "\n" else char,
                Mods(False, False, False)
            )
            for char in chars
        )

    text.clear()

def read_keys():
    """
    Yield input events.

    http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
    """
    MAX_BYTES = 2048
    ARR_TYPE = INPUT_RECORD * MAX_BYTES
    input_records = ARR_TYPE()

    windll.kernel32.ReadConsoleInputW(
        STDIN_HANDLE, pointer(input_records), MAX_BYTES, pointer(DWORD(0))
    )

    text = [ ]
    for ir in input_records:
        match ev := getattr(ir.Event, EventTypes.get(ir.EventType, ""), None):
            case KEY_EVENT_RECORD() if ev.KeyDown:
                match _handle_key(ev):
                    case None:
                        continue
                    case KeyPressEvent(Key.Enter, (False, False, False)):
                        text.append("\n")
                    case KeyPressEvent(key, (alt, ctrl, _)) as key_press_event if isinstance(key, Key) or alt or ctrl:
                        if text:
                            yield from _purge(text)
                        yield key_press_event
                    case KeyPressEvent(char, _):
                        text.append(char)

            case MOUSE_EVENT_RECORD():
                if text:
                    yield from _purge(text)
                yield _handle_mouse(ev)

    yield from _purge(text)
