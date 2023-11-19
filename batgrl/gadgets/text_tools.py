"""Tools for text."""
import numpy as np
from numpy.typing import NDArray
from wcwidth import wcswidth, wcwidth

from ..geometry import Size
from ._batgrl_markdown import find_md_tokens

__all__ = [
    "is_word_char",
    "Char",
    "style_char",
    "coerce_char",
    "parse_batgrl_md",
    "text_to_chars",
    "write_chars_to_canvas",
    "add_text",
    "binary_to_box",
    "binary_to_braille",
    "smooth_vertical_bar",
    "smooth_horizontal_bar",
]


def is_word_char(char: str) -> bool:
    """
    Whether `char` is a word character.

    A character is a word character if it is alphanumeric or an underscore.

    Parameters
    ----------
    char : str
        The char to test.

    Returns
    -------
    bool
        Whether the char is a word character.
    """
    return char.isalnum() or char == "_"


Char = np.dtype(
    [
        ("char", "U1"),
        ("bold", "?"),
        ("italic", "?"),
        ("underline", "?"),
        ("strikethrough", "?"),
        ("overline", "?"),
    ]
)
"""Data type of canvas arrays."""


def style_char(
    char: str,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    overline: bool = False,
) -> NDArray[Char]:
    """
    Return a zero-dimensional `Char` array.

    The primary use for this function is to paint a styled character into a ``Char``
    array. For instance, ``my_gadget.canvas[:] = style_char("a", bold=True)`` would
    fill the canvas with bold ``a``. Alternatively, one can avoid this function by
    setting only the ``"char"`` field of a ``Char`` array, e.g.,
    ``my_gadget.canvas["char"][:] = "a"``, but the boolean styling fields won't be
    changed. Avoid setting `Char` arrays with strings; ``my_gadget.canvas[:] = "a"`` is
    incorrect, ``"a"`` will be coerced into true for all the boolean styling fields, so
    that `my_gadget` is filled with bold, italic, underline, strikethrough, and overline
    ``a``.

    Parameters
    ----------
    char : str
        A single unicode character.
    bold : bool, default: False
        Whether char is bold.
    italic : bool, default: False
        Whether char is italic.
    underline : bool, default: False
        Whether char is underlined.
    strikethrough : bool, default: False
        Whether char is strikethrough.
    overline : bool, default: False
        Whether char is overlined.

    Returns
    -------
    NDArray[Char]
        A zero-dimensional `Char` array with the styled character.
    """
    return np.array(
        (char, bold, italic, underline, strikethrough, overline), dtype=Char
    )


def coerce_char(
    char: NDArray[Char] | str, default: NDArray[Char] | None = None
) -> NDArray[Char] | None:
    """
    Try to coerce a string into a half-width zero-dimensional Char array.

    This is mostly an internal function for setting background/default/x characters in
    App, Gadget, Text, and a few other gadgets.

    Parameters
    ----------
    char : NDArray[Char] | str
        The character to coerce.
    default : NDArray[Char] | None, default: None
        The fallback character (or None) if character can't be coerced.

    Returns
    -------
    NDArray[Char] | None
        The coerced Char (or None).
    """
    if isinstance(char, str) and len(char) > 0 and wcwidth(char[0]) == 1:
        return style_char(char[0])
    if (
        isinstance(char, np.ndarray)
        and char.dtype == Char
        and char.shape == ()
        and wcwidth(char["char"][()]) == 1
    ):
        return char
    return default


def parse_batgrl_md(text: str) -> tuple[Size, list[list[NDArray[Char]]]]:
    """
    Parse batgrl markdown and return the minimum canvas size to fit text and
    a list of lines of styled characters.

    #### Syntax for batgrl markdown
    - italic: `*this is italic text*`
    - bold: `**this is bold text**`
    - strikethrough: `~~this is strikethrough text~~`
    - underlined: `__this is underlined text__`
    - overlined: `^^this is overlined text^^`

    Parameters
    ----------
    text : str
        The text to parse.

    Returns
    -------
    tuple[Size, list[list[Char]]]
        Minimum canvas size to fit text and a list of lines of styled characters.
    """
    NO_CHAR = style_char("")
    matches, escapes = find_md_tokens(text)
    chars = [style_char(char) for char in text]
    for before, start, end, after, style in matches:
        chars[start - before : start] = [NO_CHAR] * before
        chars[end : end + after] = [NO_CHAR] * after
        for i in range(start, end):
            chars[i][style] = True

    for i in escapes:
        chars[i] = NO_CHAR

    lines = []
    line = []
    line_width = max_width = 0

    for char in chars:
        if char["char"][()] == "\n":
            lines.append(line)
            line = []
            if line_width > max_width:
                max_width = line_width
            line_width = 0
        else:
            char_width = wcswidth(char["char"][()])
            if char_width > 0:
                line.append(char)
                line_width += char_width

    lines.append(line)
    if line_width > max_width:
        max_width = line_width

    return Size(len(lines), max_width), lines


def text_to_chars(text: str) -> tuple[Size, list[list[NDArray[Char]]]]:
    """
    Convert chars to a list of lines of styled characters and the minimum canvas size to
    fit them.

    Parameters
    ----------
    text : str
        The text to convert.

    Returns
    -------
    tuple[Size, list[list[Char]]]
        Minimum canvas size to fit text and a list of lines of styled characters.
    """
    lines = [[style_char(char) for char in line] for line in text.split("\n")]
    line_width = 0
    max_width = 0
    for line in lines:
        for char in line:
            char_width = wcswidth(char["char"][()])
            if char_width > 0:
                line_width += char_width
        if line_width > max_width:
            max_width = line_width
        line_width = 0
    return Size(len(lines), max_width), lines


def write_chars_to_canvas(lines: list[list[NDArray[Char]]], canvas: NDArray[Char]):
    """
    Write a list of lines of styled characters to a canvas array.

    Full-width characters are succeeded by empty characters.

    Parameters
    ----------
    lines : list[list[NDArray[Char]]]
        Lines to write to a canvas.

    canvas : NDArray[Char]
        Canvas array where lines are written.
    """
    _, columns = canvas.shape
    for chars, canvas_line in zip(lines, canvas):
        i = 0
        for char in chars:
            if i >= columns:
                break

            width = wcswidth(char["char"][()])
            if width <= 0:
                continue

            if width == 2 and i + 1 < columns:
                empty_char = char.copy()
                empty_char["char"] = ""
                canvas_line[i + 1] = empty_char

            canvas_line[i] = char
            i += width


def add_text(
    canvas: NDArray[Char],
    text: str,
    markdown: bool = False,
    truncate_text: bool = False,
):
    """
    Add multiple lines of text to a view of a canvas.

    If `markdown` is true, text can be styled using batgrl markdown. The syntax is:
    - italic: `*this is italic text*`
    - bold: `**this is bold text**`
    - strikethrough: `~~this is strikethrough text~~`
    - underlined: `__this is underlined text__`
    - overlined: `^^this is overlined text^^`

    Text is added starting at first index in canvas. Every new line is added on a new
    row.

    Parameters
    ----------
    canvas : NDArray[Char]
        A 1- or 2-dimensional view of a `Text` canvas.
    text : str
        Text to add to canvas.
    markdown : bool, default: False
        Whether to parse text for batgrl markdown.
    truncate_text : bool, default: False
        For text that doesn't fit on canvas, truncate text if true else raise an
        `IndexError`.
    """
    size, lines = parse_batgrl_md(text) if markdown else text_to_chars(text)
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape
    if not truncate_text and (size.height > rows or size.width > columns):
        raise IndexError("Text does not fit in canvas.")
    write_chars_to_canvas(lines, canvas)


VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"


def _smooth_bar(
    blocks: str,
    max_length: int,
    proportion: float,
    offset: float,
):
    """Create a smooth bar with given blocks."""
    if offset >= 1 or offset < 0:
        raise ValueError(
            f"Offset should greater than or equal to 0 and less than 1, but {offset} "
            "was given."
        )

    block_indices = len(blocks) - 1

    fill, partial = divmod(proportion * max_length, 1)
    fill = int(fill)

    if offset == 0.0:
        if fill == max_length:
            return (blocks[-1],) * fill

        index_partial = round(partial * block_indices)
        partial_block = blocks[index_partial]
        return (*(blocks[-1],) * fill, partial_block)

    partial += offset
    if partial > 1:
        partial -= 1
    else:
        fill -= 1

    index_offset = round(offset * block_indices)
    index_partial = round(partial * block_indices)
    offset_block = blocks[index_offset]
    partial_block = blocks[index_partial]
    return (offset_block, *(blocks[-1],) * fill, partial_block)


def smooth_vertical_bar(
    max_height: int,
    proportion: float,
    offset: float = 0.0,
    reversed: bool = False,
) -> tuple[str, ...]:
    """
    Create a vertical bar that's some proportion of max_height at an offset.

    Offset bars will return a minimum of 2 characters and the first character of the bar
    should have it's colors reversed (or, if bar is reversed, all colors should be
    reversed except first character).

    Parameters
    ----------
    max_height : int
        The height of the bar if proportion was 1.0.
    proportion : float
        The height of the bar as a proportion of the max_height.
    offset : float, default: 0.0
        Offset the bar vertically by some non-negative amount.
    reversed : bool, default: False
        Reversed vertical bar is drawn top-to-bottom and offset downwards.

    Returns
    -------
    tuple[str, ...]
        The bar as a tuple of characaters.
    """
    blocks = VERTICAL_BLOCKS[::-1] if reversed else VERTICAL_BLOCKS
    return _smooth_bar(blocks, max_height, proportion, offset)


def smooth_horizontal_bar(
    max_width: int, proportion: float, offset: float = 0.0
) -> tuple[str, ...]:
    """
    Create a horizontal bar that's some proportion of max_width at an offset.
    The first character of the bar should have it's colors reversed.

    Offset bars will return a minimum of 2 characters and the first character of the bar
    should have it's colors reversed.

    Parameters
    ----------
    max_width : int
        The width of the bar if the proportion was 1.0.
    proportion : float
        The width of the bar as a proportion of the max_width.
    offset : float, default: 0.0
        Offset the bar horizontally by some non-negative amont.

    Returns
    -------
    tuple[str, ...]
        The bar as a tuple of characters.
    """
    return _smooth_bar(HORIZONTAL_BLOCKS, max_width, proportion, offset)


_BRAILLE_ENUM = np.array([[1, 8], [2, 16], [4, 32], [64, 128]])
_BOX_ENUM = np.array([[1, 4], [2, 8]])

vectorized_chr = np.vectorize(chr)
"""Vectorized `chr`."""

vectorized_box_map = np.vectorize(" ▘▖▌▝▀▞▛▗▚▄▙▐▜▟█".__getitem__)
"""Vectorized box enum to box char."""


def binary_to_braille(array_4x2: NDArray[np.bool_]) -> NDArray[np.dtype("<U1")]:
    r"""
    Convert a (h, w, 4, 2)-shaped boolean array into a (h, w) array of braille unicode
    characters.

    Parameters
    ----------
    array_4x2 : NDArray[np.bool\_]
        A (h, w, 4, 2)-shaped boolean numpy array.

    Returns
    -------
    NDArray[np.dtype("<U1")]
        A numpy array of braille unicode characters.
    """
    return vectorized_chr(
        np.sum(array_4x2 * _BRAILLE_ENUM, axis=(2, 3), initial=0x2800)
    )


def binary_to_box(array_2x2: NDArray[np.bool_ | np.uint0]) -> NDArray[np.dtype("<U1")]:
    r"""
    Convert a (h, w, 2, 2)-shaped boolean array into a (h, w) array of box unicode
    characters.

    Parameters
    ----------
    array_2x2 : NDArray[np.bool\_]
        A (h, w, 2, 2)-shaped boolean numpy array.

    Returns
    -------
    NDArray[np.dtype("<U1")]
        A numpy array of box unicode characters.
    """
    return vectorized_box_map(np.sum(array_2x2 * _BOX_ENUM, axis=(2, 3)))
