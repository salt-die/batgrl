"""
Patch more mouse support for windows. Extra *nix mouse support found in `handler.py`.
"""
from prompt_toolkit.key_binding import KeyPress
from prompt_toolkit.keys import Keys

from ..widgets.widget_data_structures import Point

from .mouse_event import (
    MouseButton,
    MouseEventType,
    MouseEvent,
    MouseModifierKey,
    MouseModifier,
)

def patch_win32_input(win32_input):
    def _handle_mouse(ev):
        FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
        RIGHTMOST_BUTTON_PRESSED =  0x0002
        FROM_LEFT_2ND_BUTTON_PRESSED = 0x0004

        RIGHT_ALT_PRESSED = 0x0001
        LEFT_ALT_PRESSED = 0x0002
        RIGHT_CTRL_PRESSED = 0x0004
        LEFT_CTRL_PRESSED = 0x0008
        SHIFT_PRESSED = 0x0010

        MOUSE_MOVED = 0x0001
        MOUSE_WHEELED = 0x0004

        position = Point(ev.MousePosition.Y, ev.MousePosition.X)

        # Event type
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

        # Buttons
        if not ev.ButtonState:
            button = MouseButton.NO_BUTTON
        elif ev.ButtonState & FROM_LEFT_1ST_BUTTON_PRESSED:
            button = MouseButton.LEFT
        elif ev.ButtonState & RIGHTMOST_BUTTON_PRESSED:
            button = MouseButton.RIGHT
        # More buttons here:
        #     https://docs.microsoft.com/en-us/windows/console/mouse-event-record-str?redirectedfrom=MSDN
        # For now, just assume middle-mouse button.
        else:
            button = MouseButton.MIDDLE

        # Modifiers
        mods = 0
        if ev.ControlKeyState & LEFT_ALT_PRESSED or ev.ControlKeyState & RIGHT_ALT_PRESSED:
            mods |= MouseModifierKey.ALT
        if ev.ControlKeyState & LEFT_CTRL_PRESSED or ev.ControlKeyState & RIGHT_CTRL_PRESSED:
            mods |= MouseModifierKey.CONTROL
        if ev.ControlKeyState & SHIFT_PRESSED:
            mods |= MouseModifierKey.SHIFT

        modifier = MouseModifier(mods)

        data = MouseEvent(position, event_type, button, modifier)
        return [ KeyPress(Keys.WindowsMouseEvent, data) ]

    win32_input.console_input_reader._handle_mouse = _handle_mouse
