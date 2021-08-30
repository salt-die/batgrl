from ..utils import is_conemu_ansi, is_windows

def create_output():
    """
    Return an output platform specific output implementation.
    """
    if is_windows():
        from .windows10 import Windows10_Output, is_win_vt100_enabled

        if is_win_vt100_enabled():
            return Windows10_Output()

        if is_conemu_ansi():
            from .conemu import ConEmuOutput

            return ConEmuOutput()

        from .win32 import Win32Output

        return Win32Output()

    else:
        from .vt100 import Vt100_Output

        return Vt100_Output()
