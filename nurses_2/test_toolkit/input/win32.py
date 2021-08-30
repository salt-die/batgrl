import os
import sys
from asyncio import get_event_loop
from contextlib import contextmanager

import msvcrt
from ctypes import windll

from ctypes import Array, pointer
from ctypes.wintypes import DWORD, HANDLE
from typing import (
    Dict,
    Iterator,
    List,
    Optional,
)

from ...mouse.mouse_data_structures import *
from ...widgets.widget_data_structures import Point
from ...data_structures import PasteEvent
from ..eventloop.win32 import create_win32_event, wait_for_handle, wait_for_handles
from ..key_binding.key_processor import KeyPress
from ..keys import Keys
from ..win32_types import (
    INPUT_RECORD,
    KEY_EVENT_RECORD,
    MOUSE_EVENT_RECORD,
    STD_INPUT_HANDLE,
    EventTypes,
)
from .base import Input


class Win32Input(Input):
    """
    `Input` class that reads from the Windows console.
    """
    def __init__(self):
        self.console_input_reader = ConsoleInputReader()  # ? Can we combine these classes?

    @contextmanager
    def attach(self, callback):
        """
        Context manager that makes this input active in the current event loop.
        """
        handle = self.handle

        try:
            loop = get_event_loop()
            run_in_executor = loop.run_in_executor
            call_soon_threadsafe = loop.call_soon_threadsafe

            remove_event = create_win32_event()

            def ready():
                try:
                    callback()
                finally:
                    run_in_executor(None, wait)

            def wait():
                if wait_for_handles([remove_event, handle]) is remove_event:
                    windll.kernel32.CloseHandle(remove_event)
                    return

                call_soon_threadsafe(ready)

            run_in_executor(None, wait)

            yield

        finally:
            windll.kernel32.SetEvent(remove_event)

    def read_keys(self):
        return list(self.console_input_reader.read())

    def flush(self):
        pass

    @property
    def closed(self):
        return False

    @contextmanager
    def raw_mode(self):
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))
        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))

        try:
            ENABLE_ECHO_INPUT = 0x0004
            ENABLE_LINE_INPUT = 0x0002
            ENABLE_PROCESSED_INPUT = 0x0001

            windll.kernel32.SetConsoleMode(
                handle,
                original_mode.value
                & ~(ENABLE_ECHO_INPUT | ENABLE_LINE_INPUT | ENABLE_PROCESSED_INPUT),
            )

            yield

        finally:
            windll.kernel32.SetConsoleMode(handle, original_mode)

    def fileno(self):
        return sys.stdin.fileno()

    def close(self):
        pass

    @property
    def handle(self) -> HANDLE:
        return self.console_input_reader.handle


class ConsoleInputReader:
    # Keys with character data.
    mappings = {
        b"\x1b": Keys.Escape,
        b"\x00": Keys.ControlSpace,  # Control-Space (Also for Ctrl-@)
        b"\x01": Keys.ControlA,  # Control-A (home)
        b"\x02": Keys.ControlB,  # Control-B (emacs cursor left)
        b"\x03": Keys.ControlC,  # Control-C (interrupt)
        b"\x04": Keys.ControlD,  # Control-D (exit)
        b"\x05": Keys.ControlE,  # Control-E (end)
        b"\x06": Keys.ControlF,  # Control-F (cursor forward)
        b"\x07": Keys.ControlG,  # Control-G
        b"\x08": Keys.ControlH,  # Control-H (8) (Identical to '\b')
        b"\x09": Keys.ControlI,  # Control-I (9) (Identical to '\t')
        b"\x0a": Keys.ControlJ,  # Control-J (10) (Identical to '\n')
        b"\x0b": Keys.ControlK,  # Control-K (delete until end of line; vertical tab)
        b"\x0c": Keys.ControlL,  # Control-L (clear; form feed)
        b"\x0d": Keys.ControlM,  # Control-M (enter)
        b"\x0e": Keys.ControlN,  # Control-N (14) (history forward)
        b"\x0f": Keys.ControlO,  # Control-O (15)
        b"\x10": Keys.ControlP,  # Control-P (16) (history back)
        b"\x11": Keys.ControlQ,  # Control-Q
        b"\x12": Keys.ControlR,  # Control-R (18) (reverse search)
        b"\x13": Keys.ControlS,  # Control-S (19) (forward search)
        b"\x14": Keys.ControlT,  # Control-T
        b"\x15": Keys.ControlU,  # Control-U
        b"\x16": Keys.ControlV,  # Control-V
        b"\x17": Keys.ControlW,  # Control-W
        b"\x18": Keys.ControlX,  # Control-X
        b"\x19": Keys.ControlY,  # Control-Y (25)
        b"\x1a": Keys.ControlZ,  # Control-Z
        b"\x1c": Keys.ControlBackslash,  # Both Control-\ and Ctrl-|
        b"\x1d": Keys.ControlSquareClose,  # Control-]
        b"\x1e": Keys.ControlCircumflex,  # Control-^
        b"\x1f": Keys.ControlUnderscore,  # Control-underscore (Also for Ctrl-hyphen.)
        b"\x7f": Keys.Backspace,  # (127) Backspace   (ASCII Delete.)
    }

    # Keys that don't carry character data.
    keycodes = {
        # Home/End
        33: Keys.PageUp,
        34: Keys.PageDown,
        35: Keys.End,
        36: Keys.Home,
        # Arrows
        37: Keys.Left,
        38: Keys.Up,
        39: Keys.Right,
        40: Keys.Down,
        45: Keys.Insert,
        46: Keys.Delete,
        # F-keys.
        112: Keys.F1,
        113: Keys.F2,
        114: Keys.F3,
        115: Keys.F4,
        116: Keys.F5,
        117: Keys.F6,
        118: Keys.F7,
        119: Keys.F8,
        120: Keys.F9,
        121: Keys.F10,
        122: Keys.F11,
        123: Keys.F12,
    }

    LEFT_ALT_PRESSED = 0x0002
    RIGHT_ALT_PRESSED = 0x0001
    SHIFT_PRESSED = 0x0010
    LEFT_CTRL_PRESSED = 0x0008
    RIGHT_CTRL_PRESSED = 0x0004

    def __init__(self, recognize_paste=True):
        self._fdcon = None
        self.recognize_paste = recognize_paste

        self.handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

    def read(self):
        """
        Return a list of `KeyPress` instances. It won't return anything when
        there was nothing to read.  (This function doesn't block.)

        http://msdn.microsoft.com/en-us/library/windows/desktop/ms684961(v=vs.85).aspx
        """
        max_count = 2048  # Max events to read at the same time.

        read = DWORD(0)
        arrtype = INPUT_RECORD * max_count
        input_records = arrtype()

        windll.kernel32.ReadConsoleInputW(
            self.handle, pointer(input_records), max_count, pointer(read)
        )

        all_keys = [ ]
        mouse_events = [ ]

        for key in self._get_keys(read, input_records):
            (mouse_events if isinstance(key, MouseEvent) else all_keys).append(key)

        # Correct non-bmp characters that are passed as separate surrogate codes
        all_keys = tuple(self._merge_paired_surrogates(all_keys))

        if self.recognize_paste and self._is_paste(all_keys):
            key_iter = iter(all_keys)

            for key in key_iter:
                paste_text = [ ]

                while key and (not isinstance(key, Keys) or key is Keys.ControlJ):
                    paste_text.append("\n" if key is Keys.ControlJ else key)
                    key = next(gen, False)

                if paste_text:
                    yield PasteEvent("".join(paste_text))

                if key is not None:
                    yield key
        else:
            yield from all_keys

        yield from mouse_events

    def _get_keys(self, read: DWORD, input_records):
        """
        Generator that yields `KeyPress` objects from the input records.
        """
        for i in range(read.value): # TODO: Test iterating over input_records directly.
            ir = input_records[i]

            if attr := EventTypes.get(ir.EventType, False):
                ev = getattr(ir.Event, attr)

                if type(ev) == KEY_EVENT_RECORD and ev.KeyDown:
                    yield from self._event_to_key(ev)

                elif type(ev) == MOUSE_EVENT_RECORD:
                    yield self._handle_mouse(ev)

    @staticmethod
    def _merge_paired_surrogates(keys):
        """
        Combines consecutive KeyPresses with high and low surrogates into
        single characters
        """
        buffered_high_surrogate = None

        for key in keys:
            is_text = not isinstance(key, Keys)
            is_high_surrogate = is_text and "\uD800" <= key <= "\uDBFF"
            is_low_surrogate = is_text and "\uDC00" <= key <= "\uDFFF"

            if buffered_high_surrogate:
                if is_low_surrogate:
                    yield (
                        (buffered_high_surrogate + key)
                        .encode("utf-16-le", "surrogatepass")
                        .decode("utf-16-le")
                    )
                    buffered_high_surrogate = None
                else:
                    yield buffered_high_surrogate
                    buffered_high_surrogate = key

            elif is_high_surrogate:
                buffered_high_surrogate = key
            else:
                yield key

        if buffered_high_surrogate:
            yield buffered_high_surrogate

    @staticmethod
    def _is_paste(keys):
        """
        Return `True` when we should consider this list of keys as a paste
        event. Pasted text on windows will be turned into a
        `Keys.BracketedPaste` event. (It's not 100% correct, but it is probably
        the best possible way to detect pasting of text and handle that
        correctly.)
        """
        # Consider paste when it contains at least one newline and at least one
        # other character.
        text_count = 0
        newline_count = 0

        for key in keys:
            if not isinstance(key, Keys):
                text_count += 1
            elif key is Keys.ControlM:
                newline_count += 1

        return newline_count >= 1 and text_count > 1

    def _event_to_key(self, ev: KEY_EVENT_RECORD):
        """
        For this `KEY_EVENT_RECORD`, return a list of `KeyPress` instances.
        """
        control_key_state = ev.ControlKeyState
        u_char = ev.uChar.UnicodeChar

        if u_char == "\x00":
            key = self.keycodes.get(ev.VirtualKeyCode)

        else:
            key = self.mappings.get(
                u_char.encode("utf-8", "surrogatepass"),
                u_char,
            )

        if not key:
            return

        if (
            control_key_state & self.LEFT_CTRL_PRESSED
            or control_key_state & self.RIGHT_CTRL_PRESSED
        ):
            if key == " ":
                key = Keys.ControlSpace

            elif key is Keys.ControlJ:
                key = Keys.Escape

            elif control_key_state & self.SHIFT_PRESSED:
                key = {
                    Keys.Left: Keys.ControlShiftLeft,
                    Keys.Right: Keys.ControlShiftRight,
                    Keys.Up: Keys.ControlShiftUp,
                    Keys.Down: Keys.ControlShiftDown,
                    Keys.Home: Keys.ControlShiftHome,
                    Keys.End: Keys.ControlShiftEnd,
                    Keys.Insert: Keys.ControlShiftInsert,
                    Keys.PageUp: Keys.ControlShiftPageUp,
                    Keys.PageDown: Keys.ControlShiftPageDown,
                }.get(key, key)

            else:
                key = {
                    Keys.Left: Keys.ControlLeft,
                    Keys.Right: Keys.ControlRight,
                    Keys.Up: Keys.ControlUp,
                    Keys.Down: Keys.ControlDown,
                    Keys.Home: Keys.ControlHome,
                    Keys.End: Keys.ControlEnd,
                    Keys.Insert: Keys.ControlInsert,
                    Keys.Delete: Keys.ControlDelete,
                    Keys.PageUp: Keys.ControlPageUp,
                    Keys.PageDown: Keys.ControlPageDown,
                }.get(key, key)

        elif control_key_state & self.SHIFT_PRESSED:
            key = {
                Keys.Tab: Keys.BackTab,
                Keys.Left: Keys.ShiftLeft,
                Keys.Right: Keys.ShiftRight,
                Keys.Up: Keys.ShiftUp,
                Keys.Down: Keys.ShiftDown,
                Keys.Home: Keys.ShiftHome,
                Keys.End: Keys.ShiftEnd,
                Keys.Insert: Keys.ShiftInsert,
                Keys.Delete: Keys.ShiftDelete,
                Keys.PageUp: Keys.ShiftPageUp,
                Keys.PageDown: Keys.ShiftPageDown,
            }.get(key, key)

        if control_key_state & self.LEFT_ALT_PRESSED:
            yield Keys.Escape

        yield key

    def _handle_mouse(self, ev):
        FROM_LEFT_1ST_BUTTON_PRESSED = 0x0001
        RIGHTMOST_BUTTON_PRESSED =  0x0002

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

        return MouseEvent(position, event_type, button, modifier)
