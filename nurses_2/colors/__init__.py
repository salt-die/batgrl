"""

To save color lookups, much of `prompt_toolkit`'s "`Attr` to escape code" logic has been
lifted from the various `Output` classes and moved to `ColorCache`.

In this way, color lookups won't need to be performed on each render, but instead only
when painting a widget's `attrs` array.

"""
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.utils import is_conemu_ansi, is_windows

from .cache import ColorCache

__all__ = (
    "get_color_cache",
)

_CACHE = None

def get_color_cache(color_depth=None):
    """Return a platform specific color cache.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    color_depth = color_depth or ColorDepth.TRUE_COLOR

    if is_windows():
        from prompt_toolkit.output.windows10 import is_win_vt100_enabled

        if not is_win_vt100_enabled() and not is_conemu_ansi():
            from ctypes import windll

            from prompt_toolkit.output.win32 import Win32Output

            from .win32color import _Win32ColorCache

            # Patching output to accept raw windows attrs.
            def set_attr_raw(self, win_attrs):
                self._winapi(windll.kernel32.SetConsoleTextAttribute, self.hconsole, win_attrs)

            Win32Output.set_attr_raw = set_attr_raw

            _CACHE = ColorCache( _Win32ColorCache(color_depth) )
            return _CACHE

    from prompt_toolkit.output.vt100 import _EscapeCodeCache, Vt100_Output

    # Patching output to accept raw escape codes (same as `write_raw` in this case).
    Vt100_Output.set_attr_raw = Vt100_Output.write_raw

    _CACHE = ColorCache( _EscapeCodeCache(color_depth) )
    return _CACHE
