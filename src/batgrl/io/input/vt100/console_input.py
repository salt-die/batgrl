"""
Parse and create events from a VT100 input stream.

Size events aren't parsed from ansi and so are added separately to `_EVENTS` once input
is active in the event loop.
"""
import os
import re
import select
import sys
from codecs import getincrementaldecoder
from collections.abc import Iterable

from ....geometry import Point, Size
from ..events import Key, KeyEvent, PasteEvent, _PartialMouseEvent
from .ansi_escapes import ALT, ANSI_ESCAPES, NO_MODS
from .mouse_bindings import TERM_SGR, TYPICAL

DECODER = getincrementaldecoder("utf-8")("surrogateescape")
MOUSE_RE = re.compile("^" + re.escape("\x1b[") + r"(<[\d;]+[mM]|M...)\Z")
MAX_ESCAPE_LENGTH = 20
"""
Heuristic for the maximum length of an ansi escape. Longer max escape length will
lengthen searches for ansi escapes in arbitrary data from stdin.
"""
STDIN = sys.stdin.fileno()

_EVENTS = []


def read_stdin() -> str:
    """Read (non-blocking) from stdin and return it decoded."""
    if not select.select([STDIN], [], [], 0)[0]:
        return ""

    try:
        return DECODER.decode(os.read(STDIN, 1024))
    except OSError:
        return ""


def _create_mouse_event(data) -> _PartialMouseEvent | None:
    """Create a _PartialMouseEvent from ansi escapes."""
    mouse_info = None

    if data[2] == "M":  # Typical: "Esc[MaB*"
        mouse_event, x, y = map(ord, data[3:])
        mouse_info = TYPICAL.get(mouse_event)

        if x >= 0xDC00:
            x -= 0xDC00
        if y >= 0xDC00:
            y -= 0xDC00

        x -= 32
        y -= 32

    elif data[2] == "<":  # Xterm SGR: "Esc[<64;85;12M"
        mouse_event, x, y = map(int, data[3:-1].split(";"))
        mouse_info = TERM_SGR.get((mouse_event, data[-1]))

        x -= 1
        y -= 1

    if mouse_info is not None:
        _EVENTS.append(_PartialMouseEvent(Point(y, x), *mouse_info))


def _find_longest_match(data: str) -> str:
    """
    Find an ANSI escape in data.

    If an escape is found an event will be created and appended to `_EVENTS` and the
    remaining data returned.
    """
    for i in range(min(MAX_ESCAPE_LENGTH, len(data)), 0, -1):
        prefix = data[:i]
        suffix = data[i:]

        if MOUSE_RE.match(prefix) is not None:
            _create_mouse_event(prefix)
            return suffix

        match ANSI_ESCAPES.get(prefix):
            case None:
                continue
            case Key.Ignore:
                return suffix
            case Key.Paste:
                paste_end = suffix.find("\x1b[201~")
                if paste_end == -1:
                    # ! To end up here, a paste start ansi was found without the
                    # ! corresponding paste end. This shouldn't happen, so maybe an
                    # ! error should be logged. For now, instead, a paste event is
                    # ! created from the remainder of the data.
                    # ? Log this error?
                    _EVENTS.append(PasteEvent(suffix))
                    return ""
                _EVENTS.append(PasteEvent(suffix[:paste_end]))
                return suffix[paste_end + 6 :]
            case KeyEvent.ESCAPE if suffix:
                # alt + character
                _EVENTS.append(KeyEvent(suffix[0], ALT))
                return suffix[1:]
            case key:
                _EVENTS.append(key)
                return suffix

    _EVENTS.append(KeyEvent(prefix, NO_MODS))
    return suffix


def events() -> Iterable[KeyEvent | PasteEvent | Size | _PartialMouseEvent]:
    """Yield input events."""
    data = "".join(iter(read_stdin, ""))

    while data:
        data = _find_longest_match(data)

    yield from _EVENTS

    _EVENTS.clear()
