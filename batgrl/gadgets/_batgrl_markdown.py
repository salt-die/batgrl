"""
Functions and classes for parsing batgrl markdown.

batgrl's markdown can make text italic, bold, strikethrough, underlined, or overlined.

#### Syntax for batgrl markdown
- italic: `*this is italic text*`
- bold: `**this is bold text**`
- strikethrough: `~~this is strikethrough text~~`
- underlined: `__this is underlined text__`
- overlined: `^^this is overlined text^^`

This module is adapted from `https://github.com/miyuchina/mistletoe/blob/master/mistletoe/core_tokens.py`.
`mistletoe` is licensed under the MIT license.
"""
import sys
from string import punctuation
from typing import Literal
from unicodedata import category

from ..geometry import clamp

DELIMITERS = set("*_~^")
WHITESPACE = set(
    " \t\n\x0b\x0c\r\x1c\x1d\x1e\x1f\x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005"
    "\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
)
PUNCTUATION = set(punctuation) | {
    chr(i) for i in range(sys.maxunicode + 1) if category(chr(i)).startswith("P")
}

Style = Literal["italic", "bold", "strikethrough", "underline", "overline"]


class Delimiter:
    def __init__(self, start: int, end: int, text: str):
        self.delimiter = text[start]
        self.number = end - start
        self.start = start
        self.end = end
        self.open = is_opener(start, end, text)
        self.close = is_closer(start, end, text)

    def match(self, other: "Delimiter") -> tuple[int, int, int, bool, bool]:
        nchars = min(self.number, other.number)
        n = clamp(nchars, None, 2)
        self.start += n
        self.number = self.end - self.start

        other.end -= n
        other.number = other.end - other.start
        return n, self.end, other.start, self.number == 0, other.number == 0

    def closed_by(self, other: "Delimiter") -> bool:
        if self.delimiter != other.delimiter:
            return False

        if self.delimiter == "*" and (
            self.open and self.close or other.open and other.close
        ):
            return (self.number + other.number) % 3 != 0 or (
                self.number % 3 == 0 and other.number % 3 == 0
            )
        elif self.delimiter != "*":
            return self.number >= 2 and other.number >= 2
        return True


def next_closer(curr_pos: int, delimiters: list[Delimiter]) -> int | None:
    for i in range(curr_pos, len(delimiters)):
        if delimiters[i].close:
            return i
    return None


def matching_opener(
    curr_pos: int, delimiters: list[Delimiter], bottom: int
) -> int | None:
    if curr_pos > 0:
        curr_delimiter = delimiters[curr_pos]
        for i in range(curr_pos - 1, bottom, -1):
            delimiter = delimiters[i]
            if delimiter.open and delimiter.closed_by(curr_delimiter):
                return i
    return None


def preceded_by(start: int, text: str, charset: set[str]):
    preceding_char = text[start - 1] if start > 0 else " "
    return preceding_char in charset


def succeeded_by(end: int, text: str, charset: set[str]):
    succeeding_char = text[end] if end < len(text) else " "
    return succeeding_char in charset


def is_left_delimiter(start: int, end: int, text: str):
    return not succeeded_by(end, text, WHITESPACE) and (
        not succeeded_by(end, text, PUNCTUATION)
        or preceded_by(start, text, PUNCTUATION)
        or preceded_by(start, text, WHITESPACE)
    )


def is_right_delimiter(start: int, end: int, text: str):
    return not preceded_by(start, text, WHITESPACE) and (
        not preceded_by(start, text, PUNCTUATION)
        or succeeded_by(end, text, WHITESPACE)
        or succeeded_by(end, text, PUNCTUATION)
    )


def is_opener(start: int, end: int, text: str) -> bool:
    if text[start] != "_":
        return is_left_delimiter(start, end, text)
    is_right = is_right_delimiter(start, end, text)
    return is_left_delimiter(start, end, text) and (
        not is_right or (is_right and preceded_by(start, text, PUNCTUATION))
    )


def is_closer(start: int, end: int, text: str) -> bool:
    if text[start] != "_":
        return is_right_delimiter(start, end, text)
    is_left = is_left_delimiter(start, end, text)
    return is_right_delimiter(start, end, text) and (
        not is_left or (is_left and succeeded_by(end, text, PUNCTUATION))
    )


def process_emphasis(
    delimiters: list[Delimiter],
) -> list[tuple[int, int, int, int, Style]]:
    curr_pos = 0
    bottoms = dict.fromkeys("*_^~", -1)
    delimiter_to_style = {
        "*": "italic",
        "**": "bold",
        "~~": "strikethrough",
        "__": "underline",
        "^^": "overline",
    }
    matches = []

    while (curr_pos := next_closer(curr_pos, delimiters)) is not None:
        closer = delimiters[curr_pos]
        delimiter = closer.delimiter

        bottom = bottoms[delimiter]

        open_pos = matching_opener(curr_pos, delimiters, bottom)
        if open_pos is not None:
            opener = delimiters[open_pos]
            n, start, end, opener_done, closer_done = opener.match(closer)

            if delimiter == "*" or n == 2:
                matches.append(
                    (
                        n + opener.number,
                        start,
                        end,
                        n + closer.number,
                        delimiter_to_style[delimiter * n],
                    )
                )

            del delimiters[open_pos + 1 : curr_pos]
            curr_pos -= curr_pos - open_pos - 1

            if opener_done:
                delimiters.remove(opener)
                curr_pos -= 1
            if closer_done:
                delimiters.remove(closer)
                curr_pos -= 1
            if curr_pos < 0:
                curr_pos = 0
        else:
            bottom = curr_pos - 1
            bottoms[delimiter] = bottom

            if closer.open:
                curr_pos += 1
            else:
                delimiters.remove(closer)

    return matches


def find_md_tokens(
    text: str,
) -> tuple[list[tuple[int, int, int, int, Style]], list[int]]:
    delimiters = []
    escapes = []
    escaped = False
    delimiter = None
    start = 0
    i = 0
    while i < len(text):
        c = text[i]
        if c == "\\" and not escaped:
            escapes.append(i)
            escaped = True
            i += 1
            continue
        if delimiter is not None and (c != delimiter or escaped):
            delimiters.append(Delimiter(start, i if not escaped else i - 1, text))
            delimiter = None
        if delimiter is None and c in DELIMITERS and not escaped:
            delimiter = c
            start = i
        escaped = False
        i += 1
    if delimiter:
        delimiters.append(Delimiter(start, i, text))
    return process_emphasis(delimiters), escapes
