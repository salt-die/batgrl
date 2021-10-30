"""
Parser for VT100 input stream.
"""
import os
import re
import select
import sys
from codecs import getincrementaldecoder

from ....data_structures import Point
from ..events import Key, KeyPressEvent, MouseEvent, PasteEvent
from .ansi_escapes import NO_MODS, ALT, ANSI_ESCAPES
from .mouse_bindings import TERM_SGR, TYPICAL, URXVT

_MOUSE_RE        = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]+[mM]|M...)\Z")
_MOUSE_PREFIX_RE = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]*|M.{0,2})\Z")

DECODER = getincrementaldecoder("utf-8")("surrogateescape")

def read_stdin():
    """
    Read (non-blocking) from stdin and return it decoded.
    """
    fileno = sys.stdin.fileno()

    if not select.select([fileno], [], [], 0)[0]:
        return ""

    try:
        data = os.read(fileno, 2048)
    except OSError:
        data = b""

    return DECODER.decode(data)

def _create_mouse_event(data):
    """
    Create a MouseEvent from ansi escapes.
    """
    if data[2] == "M":  # Typical: "Esc[MaB*"
        mouse_event, x, y = map(ord, data[3:])
        mouse_info = TYPICAL.get(mouse_event)

        if x >= 0xDC00:
            x -= 0xDC00
        if y >= 0xDC00:
            y -= 0xDC00

        x -= 32
        y -= 32

    else:
        if data[2] == "<":  # Xterm SGR: "Esc[<64;85;12M"
            mouse_event, x, y = map(int, data[3:-1].split(";"))
            mouse_info = TERM_SGR.get((mouse_event, data[-1]))

        else:  # Urxvt: "Esc[96;14;13M"
            mouse_event, x, y = map(int, data[2:-1].split(";"))
            mouse_info = URXVT.get(mouse_event)

        x -= 1
        y -= 1

    return MouseEvent(Point(y, x), *mouse_info)


class _HasLongerMatch(dict):
    """
    Return true if key is a prefix to a longer key.
    """
    def __missing__(self, prefix):
        result = (
            bool(_MOUSE_PREFIX_RE.match(prefix))
            or any(
                key != prefix and key.startswith(prefix) for key in ANSI_ESCAPES
            )
        )

        self[prefix] = result
        return result

_HAS_LONGER_MATCH = _HasLongerMatch()


class Vt100Reader:
    """
    Reader for VT100 input stream.
    """
    def __init__(self):
        self._in_bracketed_paste = False

        self._parser = self._parser_generator()
        self._parser.send(None)  # Prime the generator.

        self._events = [ ]

    def _parser_generator(self):
        """
        State machine for parsing ansi escape sequences.
        """
        END_PASTE = "\x1b[201~"
        find_longest_match = self._find_longest_match
        data = ""

        while True:
            match (yield):
                case None:  # Flush
                    while data:
                        data = find_longest_match(data)

                case char:
                    data += char

            if self._in_bracketed_paste:
                if data.endswith(END_PASTE):
                    self._events.append(
                        PasteEvent(data.removesuffix(END_PASTE))
                    )

                    data = ""
                    self._in_bracketed_paste = False

            elif data and not _HAS_LONGER_MATCH[data]:
                data = find_longest_match(data)

    def _find_longest_match(self, data):
        """
        Iteratively look for key matches to data.
        """
        for i in range(len(data), 0, -1):
            prefix = data[:i]
            suffix = data[i:]

            if _MOUSE_RE.match(prefix) is not None:
                self._events.append(_create_mouse_event(prefix))
                return suffix

            match ANSI_ESCAPES.get(prefix):
                case None:
                    continue
                case Key.Ignore:
                    pass
                case Key.BracketedPaste:
                    self._in_bracketed_paste = True
                case KeyPressEvent.ESCAPE if len(suffix) >= 1:
                    if len(suffix) == 1:  # alt + character (probably)
                        self._events.append(KeyPressEvent(suffix, ALT))
                    else:  # an unrecognized escape sequence; entire sequence (including escape) added to events
                        self._events.append(KeyPressEvent(data, NO_MODS))
                    return ""
                case key_press:
                    self._events.append(key_press)

            return suffix

        self._events.append(KeyPressEvent(prefix, NO_MODS))
        return suffix

    def read_keys(self):
        send = self._parser.send

        while chars := read_stdin():
            for char in chars:
                send(char)

        send(None)  # Flush

        yield from self._events

        self._events.clear()
