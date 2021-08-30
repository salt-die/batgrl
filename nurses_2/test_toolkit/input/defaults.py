import sys

from ..utils import is_windows

def create_input():
    if not sys.stdin.isatty():
        raise RuntimeError("Interactive terminal required.")

    if is_windows():
        from .win32 import Win32Input

        return Win32Input()
    else:

        from .vt100 import Vt100Input

        return Vt100Input()
