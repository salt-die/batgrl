"""
Parser for VT100 input stream.
"""
import os
import re
import select
import sys
from codecs import getincrementaldecoder

from ....data_structures import Point
from ..keys import Key
from ..event_data_structures import MouseEvent, PasteEvent
from .ansi_escape_sequences import ANSI_SEQUENCES
from .mouse_bindings import TERM_SGR, TYPICAL, URXVT

_MOUSE_RE        = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]+[mM]|M...)\Z")
_MOUSE_PREFIX_RE = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]*|M.{0,2})\Z")

DECODER = getincrementaldecoder("utf-8")("surrogateescape")

def read_stdin(max_bytes=1024):
    """
    Read `max_bytes` (non-blocking) from stdin and return it decoded.
    """
    fileno = sys.stdin.fileno()

    if not select.select([fileno], [], [], 0)[0]:
        return ""

    try:
        data = os.read(fileno, max_bytes)
    except OSError:
        data = b""

    return DECODER.decode(data)

def create_mouse_event(data):
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
                value for key, value in ANSI_SEQUENCES.items()
                if key != prefix and key.startswith(prefix)
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
            char = yield

            if char is None:  # Flush
                self._in_bracketed_paste = False

                while data:
                    data = find_longest_match(data)

            else:
                data += char

                # If in bracketed paste, collect data until END_PASTE.
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
                self._events.append(create_mouse_event(prefix))
                return suffix

            if (key := ANSI_SEQUENCES.get(prefix)) is not None:
                if key is Key.BracketedPaste:
                    self._in_bracketed_paste = True
                elif isinstance(key, tuple):
                    self._events.extend(key)
                else:
                    self._events.append(key)

                return suffix

        self._events.append(prefix)
        return suffix

    def read_keys(self):
        parser = self._parser

        for char in read_stdin():
            parser.send(char)

        try:
            return self._events
        finally:
            self._events = [ ]

    def flush_keys(self):
        """
        Flush the buffer of the input stream.
        """
        self._parser.send(None)  # Flush signal

        try:
            return self._events
        finally:
            self._events = [ ]
