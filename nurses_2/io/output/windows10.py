from ctypes import byref, windll
from ctypes.wintypes import DWORD

from ...data_structures import Size
from ..win32_types import (
    CONSOLE_SCREEN_BUFFER_INFO,
    STD_INPUT_HANDLE,
    STD_OUTPUT_HANDLE,
)
from .vt100 import Vt100_Output

# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004
ENABLE_MOUSE_INPUT = 0x10
ENABLE_QUICK_EDIT_MODE = 0x0040


class Windows10_Output(Vt100_Output):
    """
    Windows 10 output.
    """
    def __init__(self, is_conemu_ansi, *args, **kwargs):
        if is_conemu_ansi:
            self._original_mode = None

        else:
            self._original_mode = DWORD(0)

            # Remember the previous console mode.
            windll.kernel32.GetConsoleMode(STD_OUTPUT_HANDLE, byref(self._original_mode))

            # Enable processing of vt100 sequences.
            windll.kernel32.SetConsoleMode(
                STD_OUTPUT_HANDLE,
                DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING),
            )

        super().__init__(*args, **kwargs)

    def enable_mouse_support(self):
        self.flush()

        original_mode = DWORD()

        windll.kernel32.GetConsoleMode(STD_INPUT_HANDLE, byref(original_mode))
        windll.kernel32.SetConsoleMode(
            STD_INPUT_HANDLE,
            (original_mode.value | ENABLE_MOUSE_INPUT) & ~ENABLE_QUICK_EDIT_MODE,
        )

    def disable_mouse_support(self):
        self.flush()

        original_mode = DWORD()

        windll.kernel32.GetConsoleMode(STD_INPUT_HANDLE, byref(original_mode))
        windll.kernel32.SetConsoleMode(
            STD_INPUT_HANDLE,
            original_mode.value & ~ENABLE_MOUSE_INPUT,
        )

    def get_size(self) -> Size:
        self.flush()

        info = CONSOLE_SCREEN_BUFFER_INFO()

        windll.kernel32.GetConsoleScreenBufferInfo(STD_OUTPUT_HANDLE, byref(info))

        height = info.srWindow.Bottom - info.srWindow.Top + 1
        width = min(info.srWindow.Right - info.srWindow.Left, info.dwSize.X - 1)

        return Size(height, width)

    def restore_console(self):
        """
        Restore console to original mode.
        """
        super().restore_console()

        if self._original_mode is not None:
            windll.kernel32.SetConsoleMode(STD_OUTPUT_HANDLE, self._original_mode)


def is_vt100_enabled():
    """
    Return True if VT100 escape sequences are supported.
    """
    # Get original console mode.
    original_mode = DWORD(0)
    windll.kernel32.GetConsoleMode(STD_OUTPUT_HANDLE, byref(original_mode))

    try:
        # Try to enable VT100 sequences.
        result = windll.kernel32.SetConsoleMode(
            STD_OUTPUT_HANDLE,
            DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING),
        )

        return result == 1
    finally:
        windll.kernel32.SetConsoleMode(STD_OUTPUT_HANDLE, original_mode)
