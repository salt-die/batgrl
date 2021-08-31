"""
Parser for VT100 input stream.
"""
import re

from ....data_structures import Point
from ..keys import Keys
from ..mouse_data_structures import MouseEvent
from ..paste_event import PasteEvent
from .ansi_escape_sequences import ANSI_SEQUENCES
from .mouse_bindings import TERM_SGR, TYPICAL, URXVT

_CPR_RE          = re.compile("^" + re.escape("\x1b[") + r"\d+;\d+R\Z")
_MOUSE_RE        = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]+[mM]|M...)\Z")
_CPR_PREFEX_RE   = re.compile("^" + re.escape("\x1b[") + r"[\d;]*\Z")
_MOUSE_PREFIX_RE = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]*|M.{0,2})\Z")

FLUSH = object()


class _HasLongMatch(dict):
    """
    Maps input sequences to a boolean indicating whether there is
    any key that starts with the sequence.
    """
    def __missing__(self, prefix):
        result = (
            bool(_CPR_PREFEX_RE.match(prefix))
            or bool(_MOUSE_PREFIX_RE.match(prefix))
            or any(
                value for key, value in ANSI_SEQUENCES.items()
                if key.startswith(prefix) and key != prefix
            )
        )

        self[prefix] = result
        return result


_HAS_LONG_MATCH = _HasLongMatch()


class Vt100Parser:
    """
    Parser for VT100 input stream.
    """
    def __init__(self, feed_key_callback):
        self.feed_key_callback = feed_key_callback
        self.reset()

    def reset(self, request=False):
        self._in_bracketed_paste = False
        self._start_parser()

    def _start_parser(self):
        """
        Start the parser coroutine.
        """
        self._input_parser = self._input_parser_generator()
        self._input_parser.send(None)

    def _get_match(self, prefix):
        """
        Return the key (or keys) that maps to this prefix.
        """
        # (hard coded) If we match a CPR response, return Keys.CPRResponse.
        # (This one doesn't fit in the ANSI_SEQUENCES, because it contains
        # integer variables.)
        if _CPR_RE.match(prefix):
            return Keys.CPRResponse

        if _MOUSE_RE.match(prefix):
            return Keys.Vt100MouseEvent

        return ANSI_SEQUENCES.get(prefix)

    def _find_longest_match(self, prefix):
        """
        Iteratively look for key matches to prefix. If a match is found pass
        the match to the call handler and return the remaining bit of the prefix.
        """
        for i in range(len(prefix), 0, -1):
            if match := self._get_match(prefix[:i]):
                self._call_handler(match, prefix[:i])
                return prefix[i:]

        self._call_handler(prefix[0], prefix[0])
        return prefix[1:]

    def _input_parser_generator(self):
        """
        Coroutine (state machine) for the input parser.
        """
        prefix = ""
        flush = False

        try:
            while True:
                # Get next character.
                c = yield

                if c is FLUSH:
                    flush = True
                else:
                    prefix += c

                while flush and prefix:
                    prefix = self._find_longest_match(prefix)

                flush = False

                if prefix and not _HAS_LONG_MATCH[prefix]:
                    prefix = self._find_longest_match(prefix)
        except Exception as e:
            raise SystemExit from e

    def _call_handler(self, key, data):
        """
        Callback to handler.
        """
        if isinstance(key, tuple):
            # Received ANSI sequence that corresponds with multiple keys
            # (probably alt+something). Handle keys individually, but only pass
            # data payload to first key.
            for i, k in enumerate(key):
                self._call_handler(k, data if i == 0 else "")
        elif key is Keys.BracketedPaste:
            self._in_bracketed_paste = True
            self._paste_buffer = ""
        elif key is Keys.Vt100MouseEvent:
            self.feed_key_callback(self.mouse_event(data))
        else:
            self.feed_key_callback(key)

    @staticmethod
    def mouse_event(data):
        """
        Create a MouseEvent.
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

    def feed(self, data):
        """
        Feed the input stream.
        """
        if self._in_bracketed_paste:
            self._paste_buffer += data

            end_mark = "\x1b[201~"
            end_index = self._paste_buffer.find(end_mark)

            if end_index != -1:  # Bracketed paste end found. Clip data.
                paste_content = self._paste_buffer[:end_index]

                self.feed_key_callback(PasteEvent(paste_content))

                self._in_bracketed_paste = False
                remaining = self._paste_buffer[end_index + len(end_mark) :]
                self._paste_buffer = ""

                self.feed(remaining)

        else:
            for i, c in enumerate(data):
                if self._in_bracketed_paste:
                    self.feed(data[i:])
                    break

                self._input_parser.send(c)

    def flush(self):
        """
        Flush the buffer of the input stream.
        """
        self._input_parser.send(FLUSH)

    def feed_and_flush(self, data):
        """
        Wrapper around ``feed`` and ``flush``.
        """
        self.feed(data)
        self.flush()
