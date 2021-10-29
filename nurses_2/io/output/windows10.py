from ctypes import byref, pointer, windll
from ctypes.wintypes import DWORD, HANDLE

from ...data_structures import Size
from ..utils import is_windows, is_conemu_ansi
from ..win32_types import (
    CONSOLE_SCREEN_BUFFER_INFO,
    STD_INPUT_HANDLE,
    STD_OUTPUT_HANDLE,
)
from .vt100 import Vt100_Output

# See: https://msdn.microsoft.com/pl-pl/library/windows/desktop/ms686033(v=vs.85).aspx
ENABLE_PROCESSED_INPUT = 0x0001
ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004


class Windows10_Output(Vt100_Output):
    """
    Windows 10 output.
    """
    def __init__(self):
        super().__init__()
        self._hconsole = HANDLE(windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE))

        if is_conemu_ansi():
            self._original_mode = None

        else:
            self._original_mode = DWORD(0)

            # Remember the previous console mode.
            windll.kernel32.GetConsoleMode(self._hconsole, byref(self._original_mode))

            # Enable processing of vt100 sequences.
            windll.kernel32.SetConsoleMode(
                self._hconsole,
                DWORD(ENABLE_PROCESSED_INPUT | ENABLE_VIRTUAL_TERMINAL_PROCESSING),
            )

    def enable_mouse_support(self):
        self.flush()
        ENABLE_MOUSE_INPUT = 0x10
        ENABLE_QUICK_EDIT_MODE = 0x0040

        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))
        windll.kernel32.SetConsoleMode(
            handle,
            (original_mode.value | ENABLE_MOUSE_INPUT) & ~ENABLE_QUICK_EDIT_MODE,
        )

    def disable_mouse_support(self):
        self.flush()
        ENABLE_MOUSE_INPUT = 0x10
        handle = HANDLE(windll.kernel32.GetStdHandle(STD_INPUT_HANDLE))

        original_mode = DWORD()
        windll.kernel32.GetConsoleMode(handle, pointer(original_mode))
        windll.kernel32.SetConsoleMode(
            handle,
            original_mode.value & ~ENABLE_MOUSE_INPUT,
        )

    def get_size(self) -> Size:
        self.flush()

        info = CONSOLE_SCREEN_BUFFER_INFO()

        windll.kernel32.GetConsoleScreenBufferInfo(self._hconsole, byref(info))

        height = info.srWindow.Bottom - info.srWindow.Top + 1
        width = min(info.srWindow.Right - info.srWindow.Left, info.dwSize.X - 1)

        return Size(height, width)

    def restore_console(self):
        """
        Restore console to original mode.
        """
        if self._original_mode is not None:
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
