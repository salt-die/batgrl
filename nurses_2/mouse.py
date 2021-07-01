from prompt_toolkit.keys import Keys
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType

__all__ = (
    "MouseEvent",
    "MouseEventType",
    "handle_mouse",
)

def create_mouse_event(key_press):
    """Create MouseEvent from a KeyPress.
    """
    # This is the mostly the same as /prompt_toolkit/key_binding/bindings/mouse.py
    # Reimplented for `nurses` to avoid `prompt_toolkit`'s KeyBinding class.
    # (`nurses` dispatches input differently.)

    EVENTS = {
        32: MouseEventType.MOUSE_DOWN,
        35: MouseEventType.MOUSE_UP,
        96: MouseEventType.SCROLL_UP,
        97: MouseEventType.SCROLL_DOWN,
        (0, "M"): MouseEventType.MOUSE_DOWN,
        (0, "m"): MouseEventType.MOUSE_UP,
        (64, "M"): MouseEventType.SCROLL_UP,
        (65, "M"): MouseEventType.SCROLL_DOWN,
    }

    if key_press.key == Keys.Vt100MouseEvent:
        # Examples of `key_press.data`:
        #   * Typical:   "Esc[MaB*"
        #   * Xterm SGR: "Esc[<64;85;12M"
        #   * Urxvt:     "Esc[96;14;13M"
        data = key_press.data

        if data[2] == "M":  # Typical
            mouse_event, x, y = map(ord, data[3:])
            mouse_event_type = EVENTS.get(mouse_event)

            if x >= 0xDC00:
                x -= 0xDC00
            if y >= 0xDC00:
                y -= 0xDC00

            x -= 32
            y -= 32

        else:
            if data[2] == "<":  # Xterm SGR
                mouse_event, x, y = map(int, data[3:-1].split(";"))
                mouse_event_type = EVENTS.get((mouse_event, data[-1]))

            else:  # Urxvt
                mouse_event, x, y = map(int, data[2:-1].split(";"))
                mouse_event_type = EVENTS.get(mouse_event)

            x -= 1
            y -= 1

    else:
        mouse_event, *coords = key_press.data.split(";")
        mouse_event_type = MouseEventType(mouse_event)
        x, y = map(int, coords)

    return MouseEvent(position=(y, x), event_type=mouse_event_type)  # y, x swapped for nurses compatibility
