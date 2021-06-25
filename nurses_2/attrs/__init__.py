"""
To save color lookups, `prompt_toolkit`'s "`Attr` to escape code" logic has been
lifted from Vt100_Output and moved to `nurses`' `_EscapeCodeCache`.

In this way, color lookups won't need to be performed on each render, but instead only
when painting a widget's `attrs` array.
"""
from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.utils import is_conemu_ansi, is_windows

from ._escape_code_cache import _EscapeCodeCache

__all__ = (
    "get_color_cache",
)

_CACHE = None

def get_escape_code_cache(color_depth=None):
    """
    Return a platform specific color cache.
    """
    global _CACHE
    if _CACHE is not None:
        return _CACHE

    color_depth = color_depth or ColorDepth.TRUE_COLOR

    if is_windows():
        from prompt_toolkit.output.windows10 import is_win_vt100_enabled

        if not is_win_vt100_enabled() and not is_conemu_ansi():
            raise RuntimeError("non-vt100 enabled consoles not supported")

    _CACHE = _EscapeCodeCache(color_depth)
    return _CACHE
