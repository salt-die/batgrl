"""
To save color lookups, much of `prompt_toolkit`'s "`Attr` to escape code" logic has been
lifted from the various `Output` classes.
"""
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.output.vt100 import _EscapeCodeCache
from prompt_toolkit.utils import is_conemu_ansi, is_windows

_CACHE = None

def get_color_cache(color_depth=None):
    """
    Return a platform specific color cache.

    Caches take a `prompt_toolkit` `Attr` and return a corresponding escape code or
    win32 color.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    color_depth = color_depth or ColorDepth.TRUE_COLOR

    if is_windows():
        from prompt_toolkit.output.windows10 import is_win_vt100_enabled
        from prompt_toolkit.output.win32 import Win32Output

        if not is_win_vt100_enabled() and not is_conemu_ansi():
            from ctypes import windll

            from .win32color import _Win32ColorCache

            def write_raw(self, win_attrs):
                self._winapi(windll.kernel32.SetConsoleTextAttribute, self.hconsole, win_attrs)

            Win32Output.write_raw = write_raw

            _CACHE = _Win32ColorCache(color_depth)
            return _CACHE

    _CACHE = _EscapeCodeCache(color_depth)
    return _CACHE
