"""
Parser for VT100 input stream.
"""
import re

from ...mouse import MouseEvent
from ...mouse.create_vt100_mouse_event import create_vt100_mouse_event as mouse_event
from ...data_structures import PasteEvent
from ..keys import Keys
from .ansi_escape_sequences import ANSI_SEQUENCES

_cpr_response_re = re.compile("^" + re.escape("\x1b[") + r"\d+;\d+R\Z")
_mouse_event_re = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]+[mM]|M...)\Z")

_cpr_response_prefix_re = re.compile("^" + re.escape("\x1b[") + r"[\d;]*\Z")
_mouse_event_prefix_re = re.compile("^" + re.escape("\x1b[") + r"(<?[\d;]*|M.{0,2})\Z")

FLUSH = object()


class _IsPrefixOfLongerMatchCache(dict):
    """
    Dictionary that maps input sequences to a boolean indicating whether there is
    any key that start with this characters.
    """

    def __missing__(self, prefix):
        result = (
            bool(_cpr_response_prefix_re.match(prefix))
            or bool(_mouse_event_prefix_re.match(prefix))
            or any(
                value
                for key, value in ANSI_SEQUENCES.items()
                if key.startswith(prefix) and key != prefix
            )
        )

        self[prefix] = result
        return result


_IS_PREFIX_OF_LONGER_MATCH_CACHE = _IsPrefixOfLongerMatchCache()


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
        if _cpr_response_re.match(prefix):
            return Keys.CPRResponse

        if _mouse_event_re.match(prefix):
            return Keys.Vt100MouseEvent

        return ANSI_SEQUENCES.get(prefix)

    def _input_parser_generator(self):
        """
        Coroutine (state machine) for the input parser.
        """
        prefix = ""
        retry = False
        flush = False

        while True:
            flush = False

            if retry:
                retry = False
            else:
                # Get next character.
                c = yield

                if c is FLUSH:
                    flush = True
                else:
                    prefix += c

            # If we have some data, check for matches.
            if prefix:
                is_prefix_of_longer_match = _IS_PREFIX_OF_LONGER_MATCH_CACHE[prefix]

                # Exact matches found, call handlers..
                if flush or not is_prefix_of_longer_match:
                    if match := self._get_match(prefix):
                        self._call_handler(match, prefix)
                        prefix = ""

                    else:
                        retry = True

                        # Loop over the input, try the longest match first and
                        # shift.
                        for i in range(len(prefix), 0, -1):
                            if match := self._get_match(prefix[:i]):
                                self._call_handler(match, prefix[:i])
                                prefix = prefix[i:]
                                break
                        else:
                            self._call_handler(prefix[0], prefix[0])
                            prefix = prefix[1:]

    def _call_handler(self, key, insert_text):
        """
        Callback to handler.
        """
        if isinstance(key, tuple):
            # Received ANSI sequence that corresponds with multiple keys
            # (probably alt+something). Handle keys individually, but only pass
            # data payload to first key.
            for i, k in enumerate(key):
                self._call_handler(k, insert_text if i == 0 else "")
        elif key is Keys.BracketedPaste:
            self._in_bracketed_paste = True
            self._paste_buffer = ""
        elif key is Keys.Vt100MouseEvent:
            self.feed_key_callback(mouse_event(insert_text))
        else:
            self.feed_key_callback(key)

    def feed(self, data):
        """
        Feed the input stream.
        """
        if self._in_bracketed_paste:
            self._paste_buffer += data
            end_mark = "\x1b[201~"

            end_index = self._paste_buffer.find(end_mark)
            if end_index != -1:
                # Feed content to key bindings.
                paste_content = self._paste_buffer[:end_index]
                self.feed_key_callback(PasteEvent(paste_content))

                # Quit bracketed paste mode and handle remaining input.
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
