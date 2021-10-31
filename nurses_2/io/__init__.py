import sys
from contextlib import contextmanager

from .environ import is_conemu_ansi, is_windows
from .input.events import (
    Key,
    Mods,
    KeyPressEvent,
    MouseEventType,
    MouseButton,
    MouseEvent,
    PasteEvent,
)

__all__ = (
    "Key",
    "Mods",
    "KeyPressEvent",
    "MouseEventType",
    "MouseButton",
    "MouseEvent",
    "PasteEvent",
    "io",
)

def _create_io():
    """
    Return a platform specific io.
    """
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required.")

    if is_windows():
        from .output.windows10 import is_vt100_enabled, Windows10_Output

        if not is_conemu_ansi() and not is_vt100_enabled():
            raise RuntimeError("nurses_2 not supported on non-vt100 enabled terminals")

        from .input.win32 import win32_input

        return win32_input, Windows10_Output()

    else:
        from .input.vt100 import vt100_input
        from .output.vt100 import Vt100_Output

        return vt100_input, Vt100_Output()

@contextmanager
def io():
    """
    Initialize and return input and output.
    """
    env_in, env_out = _create_io()

    env_out.enable_mouse_support()
    env_out.enable_bracketed_paste()
    env_out.enter_alternate_screen()
    env_out.flush()

    try:
        yield env_in, env_out

    finally:
        env_out.quit_alternate_screen()
        env_out.reset_attributes()
        env_out.disable_mouse_support()
        env_out.disable_bracketed_paste()
        env_out.show_cursor()
        env_out.flush()
        env_out.restore_console()
