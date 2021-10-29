import sys

from .utils import is_conemu_ansi, is_windows
from .input.mouse_data_structures import MouseEventType, MouseButton
from .input.event_data_structures import Mods, KeyPressEvent, MouseEvent, PasteEvent
from .input.keys import Key

__all__ = (
    "create_io",
    "MouseEventType",
    "MouseButton",
    "Mods",
    "KeyPressEvent",
    "MouseEvent",
    "PasteEvent",
    "Key",
)

def create_io():
    """
    Return a platform specific io.
    """
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required.")

    if is_windows():
        from .output.windows10 import is_win_vt100_enabled, Windows10_Output

        if not (is_conemu_ansi() or is_win_vt100_enabled()):
            raise RuntimeError("nurses_2 not supported on non-vt100 enabled terminals")

        from .input.win32 import win32_input  # Note we return a namespace and not a class.

        return win32_input, Windows10_Output()

    else:
        from .input.vt100 import Vt100Input
        from .output.vt100 import Vt100_Output

        return Vt100Input(), Vt100_Output()
