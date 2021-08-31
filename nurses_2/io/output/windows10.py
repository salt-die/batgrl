from functools import wraps

from ctypes import byref, pointer, windll
from ctypes.wintypes import DWORD, HANDLE

from ...data_structures import Size
from ..utils import is_windows
from ..win32_types import (
    CONSOLE_SCREEN_BUFFER_INFO,
    SMALL_RECT,
    STD_INPUT_HANDLE,
    STD_OUTPUT_HANDLE,
)
from .vt100 import Vt100_Output

# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

def flush_before(method):
    """
    Decorator that calls `flush` before calling the method.
    """
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        self.flush()
        method(self, *args, **kwargs)

    return wrapper


class Windows10_Output(Vt100_Output):
    """
    Windows 10 output.
    """
    def __init__(self):
        super().__init__()
        self._hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))

        self._original_mode = DWORD(0)

        # Remember the previous console mode.
        windll.kernel32.GetConsoleMode(self._hconsole, byref(self._original_mode))

        # Enable processing of vt100 sequences.
        windll.kernel32.SetConsoleMode(
            self._hconsole,
            DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING),
        )

    def get_win32_screen_buffer_info(self) -> CONSOLE_SCREEN_BUFFER_INFO:
        """
        Return Screen buffer info.
        """
        # NOTE: `GetConsoleScreenBufferInfo` causes Python to crash on certain 64bit
        #     Python versions. (Reproduced with 64bit Python 2.7.6, on Windows 10).

        # The Python documentation contains the following - possibly related - warning:
        #     ctypes does not support passing unions or structures with
        #     bit-fields to functions by value. While this may work on 32-bit
        #     x86, it's not guaranteed by the library to work in the general
        #     case. Unions and structures with bit-fields should always be
        #     passed to functions by pointer.

        # Also see:
        #    - https://github.com/ipython/ipython/issues/10070
        #    - https://github.com/jonathanslenders/python-prompt-toolkit/issues/406
        #    - https://github.com/jonathanslenders/python-prompt-toolkit/issues/86

        self.flush()
        sbinfo = CONSOLE_SCREEN_BUFFER_INFO()
        success = windll.kernel32.GetConsoleScreenBufferInfo(
            self._hconsole, byref(sbinfo)
        )

        if success:
            return sbinfo
        else:
            raise RuntimeError("Not in a windows console.")

    def get_rows_below_cursor_position(self):
        info = self.get_win32_screen_buffer_info()
        return info.srWindow.Bottom - info.dwCursorPosition.Y + 1

    @flush_before
    def scroll_buffer_to_prompt(self):
        """
        To be called before drawing the prompt. This should scroll the console
        to left, with the cursor at the bottom (if possible).
        """
        # Get current window size
        info = self.get_win32_screen_buffer_info()
        sr = info.srWindow
        cursor_pos = info.dwCursorPosition

        result = SMALL_RECT()

        # Scroll to the left.
        result.Left = 0
        result.Right = sr.Right - sr.Left

        # Scroll vertical
        win_height = sr.Bottom - sr.Top
        if 0 < sr.Bottom - cursor_pos.Y < win_height - 1:
            # no vertical scroll if cursor already on the screen
            result.Bottom = sr.Bottom
        else:
            result.Bottom = max(win_height, cursor_pos.Y)
        result.Top = result.Bottom - win_height

        # Scroll API
        windll.kernel32.SetConsoleWindowInfo(self._hconsole, True, byref(result))

    @flush_before
    def enable_mouse_support(self):
        ENABLE_MOUSE_INPUT = 0x10

        # This `ENABLE_QUICK_EDIT_MODE` flag needs to be cleared for mouse
        # support to work, but it's possible that it was already cleared
        # before.
        ENABLE_QUICK_EDIT_MODE = 0x0040

        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))
        windll.kernel32.SetConsoleMode(
            handle,
            (original_mode.value | ENABLE_MOUSE_INPUT) & ~ENABLE_QUICK_EDIT_MODE,
        )

    @flush_before
    def disable_mouse_support(self):
        ENABLE_MOUSE_INPUT = 0x10
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))
        windll.kernel32.SetConsoleMode(
            handle,
            original_mode.value & ~ENABLE_MOUSE_INPUT,
        )

    def get_size(self) -> Size:
        info = self.get_win32_screen_buffer_info()

        width = info.srWindow.Right - info.srWindow.Left

        height = info.srWindow.Bottom - info.srWindow.Top + 1

        # We avoid the right margin, windows will wrap otherwise.
        maxwidth = info.dwSize.X - 1
        width = min(maxwidth, width)

        return Size(height, width)

    def restore_console(self):
        """
        Restore console to original mode.
        """
        windll.kernel32.SetConsoleMode(self._hconsole, self._original_mode)


def is_win_vt100_enabled() -> bool:
    """
    Returns True when we're running Windows and VT100 escape sequences are
    supported.
    """
    if not is_windows():
        return False

    hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))

    # Get original console mode.
    original_mode = DWORD(0)
    windll.kernel32.GetConsoleMode(hconsole, byref(original_mode))

    try:
        # Try to enable VT100 sequences.
        result = windll.kernel32.SetConsoleMode(
            hconsole, DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING)
        )

        return result == 1
    finally:
        windll.kernel32.SetConsoleMode(hconsole, original_mode)
