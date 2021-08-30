from ..widgets.widget_data_structures import Point
from .mouse_data_structures import *
from .bindings import TERM_SGR, TYPICAL, URXVT

def create_vt100_mouse_event(data):
    """
    Create a MouseEvent.
    """
    if data[2] == "M":  # Typical: "Esc[MaB*"
        mouse_event, x, y = map(ord, data[3:])
        mouse_info = TYPICAL.get(mouse_event)

        if x >= 0xDC00:
            x -= 0xDC00
        if y >= 0xDC00:
            y -= 0xDC00

        x -= 32
        y -= 32

    else:
        if data[2] == "<":  # Xterm SGR: "Esc[<64;85;12M"
            mouse_event, x, y = map(int, data[3:-1].split(";"))
            mouse_info = TERM_SGR.get((mouse_event, data[-1]))

        else:  # Urxvt: "Esc[96;14;13M"
            mouse_event, x, y = map(int, data[2:-1].split(";"))
            mouse_info = URXVT.get(mouse_event)

        x -= 1
        y -= 1

    return MouseEvent(Point(y, x), *mouse_info)  # y, x swapped for nurses compatibility
