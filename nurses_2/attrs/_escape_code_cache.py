from prompt_toolkit.output.vt100 import _EscapeCodeCache as _PTEscapeCodeCache


class _EscapeCodeCache:
    """
    Cache of escape codes.
    """
    __slots__ = (
        '_escape_code_cache',
        '_aliases',
    )

    def __init__(self, color_depth):
        self._escape_code_cache = _PTEscapeCodeCache(color_depth)
        self._aliases = { }

    def escape_code(
        self,
        fg_color='',
        bg_color='',
        *,
        bold=False,
        underline=False,
        italic=False,
        blink=False,
        reverse=False,
        alias=None
    ):
        """
        Return an escape code with specified styling.

        Notes
        -----
        If an alias is provided, the escape code can be returned later by providing the
        alias for `fg_color` (other parameters will be ignored).
        """
        aliases = self._aliases

        if fg_color in aliases:
            return aliases[fg_color]

        escape_code = self._escape_code_cache[
            (fg_color, bg_color, bold, underline, italic, blink, reverse, False)
        ]

        if alias is not None:
            aliases[alias] = escape_code

        return escape_code
