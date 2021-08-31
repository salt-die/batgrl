import sys

from .utils import is_conemu_ansi, is_windows
from .input.mouse_data_structures import *
from .input.paste_event import PasteEvent
from .input.keys import Key

__all__ = (
    "create_input",
    "create_output",
    "MouseEventType",
    "MouseButton",
    "MouseModifier",
    "MouseModifierKey",
    "MouseEvent",
    "PasteEvent",
    "Key",
)

def create_input():
    """
    Return a platform specific input implementation.
    """
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required.")

    if is_windows():
        from .input.win32 import Win32Input
        return Win32Input()

    else:
        from .input.vt100 import Vt100Input
        return Vt100Input()

def create_output():
    """
    Return a platform specific output implementation.
    """
    if is_windows():
        from .output.windows10 import is_win_vt100_enabled, Windows10_Output

        if is_win_vt100_enabled():
            return Windows10_Output()

        if is_conemu_ansi():
            from .output.conemu import ConEmuOutput
            return ConEmuOutput()

        raise RuntimeError("nurses_2 not supported on non-vt100 enabled terminals")

    else:
        from .output.vt100 import Vt100_Output
        return Vt100_Output()
