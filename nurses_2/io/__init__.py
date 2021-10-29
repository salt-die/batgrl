import sys

from .utils import is_conemu_ansi, is_windows
from .input.events import (
    Key,
    Mods,
    KeyPressEvent,
    MouseEventType,
    MouseButton,
    MouseEvent,
    PasteEvent,
)
from .input.keys import Key

__all__ = (
    "Key",
    "Mods",
    "KeyPressEvent",
    "MouseEventType",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
    "create_io",
)

def create_io():
    """
    Return a platform specific io.
    """
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required.")

    if is_windows():
        from .output.windows10 import is_win_vt100_enabled, Windows10_Output

        if not is_conemu_ansi() or not is_win_vt100_enabled():
            raise RuntimeError("nurses_2 not supported on non-vt100 enabled terminals")

        from .input.win32 import win32_input

        return win32_input, Windows10_Output()

    else:
        from .input.vt100 import vt100_input
        from .output.vt100 import Vt100_Output

        return vt100_input, Vt100_Output()
