from ctypes import byref

from prompt_toolkit.output.color_depth import ColorDepth
from prompt_toolkit.output.win32 import ColorLookupTable, NoConsoleScreenBufferError
from prompt_toolkit.win32_types import CONSOLE_SCREEN_BUFFER_INFO


class _Win32ColorCache:
    __slots__ = (
        'color_depth',
        '_color_lookup',
        '_attrs_cache',
    )

    def __init__(self, color_depth):
        self.color_depth = color_depth
        self._color_lookup = ColorLookupTable()
        self._attrs_cache = { }

        ### Default colors ########################################
        sbinfo = CONSOLE_SCREEN_BUFFER_INFO()                     #
        success = windll.kernel32.GetConsoleScreenBufferInfo(     #
            self.hconsole, byref(sbinfo)                          #
        )                                                         #
                                                                  #
        if not success:                                           #
            raise NoConsoleScreenBufferError                      #
                                                                  #
        self.default_attrs = sbinfo.wAttributes if sbinfo else 15 #
        ###########################################################

    def __getitem__(self, attrs):
        fgcolor, bgcolor, _, _, _, _, reverse, _ = attrs
        attrs = fgcolor, bgcolor, reverse
        attrs_cache = self._attrs_cache

        if attrs not in attrs_cache:
            win_attrs = self.default_attrs
            color_lookup = self._color_lookup

            if color_depth != ColorDepth.DEPTH_1_BIT:
                if fgcolor:
                    win_attrs &= ~0xF
                    win_attrs |= color_lookup.lookup_fg_color(fgcolor)

                if bgcolor:
                    win_attrs &= ~0xF0
                    win_attrs |= color_lookup.lookup_bg_color(bgcolor)

            if reverse:
                 win_attrs = (
                     (win_attrs & ~0xFF)
                     | ((win_attrs & 0xF) << 4)
                     | ((win_attrs & 0xF0) >> 4)
                 )

            attrs_cache[attrs] = win_attrs

        return attrs_cache[attrs]
