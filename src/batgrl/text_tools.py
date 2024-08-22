"""Tools for text."""

from bisect import bisect
from functools import lru_cache
from operator import itemgetter

import numpy as np
from numpy.typing import NDArray

from ._batgrl_markdown import find_md_tokens
from ._char_widths import CHAR_WIDTHS
from .colors import BLACK, WHITE, Color
from .geometry import Size

__all__ = [
    "Cell",
    "add_text",
    "binary_to_box",
    "binary_to_braille",
    "new_cell",
    "char_width",
    "coerce_cell",
    "is_word_char",
    "smooth_horizontal_bar",
    "smooth_vertical_bar",
    "str_width",
]

VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"
_BRAILLE_ENUM = np.array([[1, 8], [2, 16], [4, 32], [64, 128]])
_BOX_ENUM = np.array([[1, 4], [2, 8]])

_vectorized_chr = np.vectorize(chr)
"""Vectorized `chr`."""

_vectorized_box_map = np.vectorize(" ▘▖▌▝▀▞▛▗▚▄▙▐▜▟█".__getitem__)
"""Vectorized box enum to box char."""


@lru_cache(maxsize=1024)
def char_width(char: str) -> int:
    """
    Return the column width of a character.

    Parameters
    ----------
    char : str
        A unicode character.

    Returns
    -------
    int
        The character column width.
    """
    if char == "":
        return 0

    char_ord = ord(char)
    i = bisect(CHAR_WIDTHS, char_ord, key=itemgetter(0))
    if i == 0:
        return 1

    _, high, width = CHAR_WIDTHS[i - 1]
    if char_ord <= high:
        return width

    return 1


@lru_cache(maxsize=256)
def str_width(chars: str) -> int:
    """
    Return the total column width of a string.

    Parameters
    ----------
    chars : str
        A string.

    Returns
    -------
    int
        The total column width of the string.
    """
    return sum(map(char_width, chars))


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


Cell = np.dtype(
    [
        ("char", "U1"),
        ("bold", "?"),
        ("italic", "?"),
        ("underline", "?"),
        ("strikethrough", "?"),
        ("overline", "?"),
        ("reverse", "?"),
        ("fg_color", "u1", (3,)),
        ("bg_color", "u1", (3,)),
    ]
)
"""A structured array type that represents a single cell in a terminal."""


@lru_cache
def cell_sans(*names: str) -> list[str]:
    r"""
    Return all fields of ``Cell`` not in names.

    Parameters
    ----------
    \*names : str
        Excluded fields of ``Cell``.

    Returns
    -------
    list[str]
        All fields of ``Cell`` not in names.
    """
    return [name for name in Cell.names if name not in names]


def new_cell(
    char: str = " ",
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    overline: bool = False,
    reverse: bool = False,
    fg_color: Color = WHITE,
    bg_color: Color = BLACK,
) -> NDArray[Cell]:
    """
    Create a ``Cell`` scalar.

    A Cell is a structured array type that represents a single cell in a terminal.

    Parameters
    ----------
    char : str, default: " "
        The cell's character.
    bold : bool, default: False
        Whether cell is bold.
    italic : bool, default: False
        Whether cell is italic.
    underline : bool, default: False
        Whether cell is underlined.
    strikethrough : bool, default: False
        Whether cell is strikethrough.
    overline : bool, default: False
        Whether cell is overlined.
    fg_color : Color, default: WHITE
        Foreground color of cell.
    bg_color : Color, default: BLACK
        Background color of cell.

    Returns
    -------
    NDArray[Cell]
        A ``Cell`` scalar.
    """
    return np.array(
        (
            char,
            bold,
            italic,
            underline,
            strikethrough,
            overline,
            reverse,
            fg_color,
            bg_color,
        ),
        dtype=Cell,
    )


def coerce_cell(char: NDArray[Cell] | str, default: NDArray[Cell]) -> NDArray[Cell]:
    """
    Try to coerce a string or ``Cell`` scalar into a half-width ``Cell`` scalar.

    Parameters
    ----------
    char : NDArray[Cell] | str
        The character to coerce.
    default : NDArray[Cell] | None, default: None
        The fallback character (or None) if character can't be coerced.

    Returns
    -------
    NDArray[Cell] | None
        The coerced Cell or None if character can't be coerced.
    """
    if isinstance(char, str) and len(char) > 0 and char_width(char[0]) == 1:
        return new_cell(char=char[0])
    if (
        isinstance(char, np.ndarray)
        and char.dtype == Cell
        and char.shape == ()
        and char_width(char["char"].item()) == 1
    ):
        return char
    return default


def _parse_batgrl_md(text: str) -> tuple[Size, list[list[NDArray[Cell]]]]:
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
    tuple[Size, list[list[Cell]]]
        Minimum canvas size to fit text and a list of lines of styled characters.
    """
    NO_CHAR = new_cell(char="")
    matches, escapes = find_md_tokens(text)
    cells = [new_cell(char=char)[cell_sans("fg_color", "bg_color")] for char in text]
    for before, start, end, after, style in matches:
        cells[start - before : start] = [NO_CHAR] * before
        cells[end : end + after] = [NO_CHAR] * after
        for i in range(start, end):
            cells[i][style] = True

    for i in escapes:
        cells[i] = NO_CHAR

    lines = []
    line = []
    line_width = max_width = 0

    for cell in cells:
        char = cell["char"].item()
        if char == "":
            continue

        if char == "\n":
            lines.append(line)
            line = []
            if line_width > max_width:
                max_width = line_width
            line_width = 0
        else:
            width = char_width(char)
            line_width += width
            if width > 0:
                line.append(cell)

    lines.append(line)
    if line_width > max_width:
        max_width = line_width

    return Size(len(lines), max_width), lines


def _text_to_cells(text: str) -> tuple[Size, list[list[NDArray[Cell]]]]:
    """
    Convert some text to a list of lists of Cells and the minimum canvas size to fit
    them.

    Parameters
    ----------
    text : str
        The text to convert.

    Returns
    -------
    tuple[Size, list[list[Cell]]]
        Minimum canvas size to fit text and a list of lists of Cells.
    """
    lines = [
        [new_cell(char=char)[cell_sans("fg_color", "bg_color")] for char in line]
        for line in text.split("\n")
    ]
    max_width = 0
    for line in lines:
        line_width = 0
        for char in line:
            width = char_width(char["char"].item())
            line_width += width
        if line_width > max_width:
            max_width = line_width
    return Size(len(lines), max_width), lines


def _write_lines_to_canvas(lines, canvas, fg_color, bg_color):
    """Write a list of lists of Cells to a canvas array."""
    _, columns = canvas.shape
    for cells, canvas_line, fg, bg in zip(
        lines,
        canvas[cell_sans("fg_color", "bg_color")],
        canvas["fg_color"],
        canvas["bg_color"],
    ):
        i = 0
        for cell in cells:
            if i >= columns:
                break

            width = char_width(cell["char"].item())
            if width == 0:
                continue

            canvas_line[i] = cell
            if fg_color is not None:
                fg[i] = fg_color
            if bg_color is not None:
                bg[i] = bg_color

            if width == 2 and i + 1 < columns:
                empty_cell = cell.copy()
                empty_cell["char"] = ""
                canvas_line[i + 1] = empty_cell
                if fg_color is not None:
                    fg[i + 1] = fg_color
                if bg_color is not None:
                    bg[i + 1] = bg_color

            i += width


def add_text(
    canvas: NDArray[Cell],
    text: str,
    *,
    fg_color: Color | None = None,
    bg_color: Color | None = None,
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
    canvas : NDArray[Cell]
        A 1- or 2-dimensional view of a `Text` canvas.
    text : str
        Text to add to canvas.
    fg_color : Color | None, default: None
        Foreground color of text. If not given, current canvas foreground color is used.
    bg_color : Color | None, default: None
        Background color of text. If not given, current canvas background color is used.
    markdown : bool, default: False
        Whether to parse text for batgrl markdown.
    truncate_text : bool, default: False
        For text that doesn't fit on canvas, truncate text if true else raise an
        `IndexError`.
    """
    size, lines = _parse_batgrl_md(text) if markdown else _text_to_cells(text)
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape
    if not truncate_text and (size.height > rows or size.width > columns):
        raise IndexError("Text does not fit in canvas.")
    _write_lines_to_canvas(lines, canvas, fg_color, bg_color)


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
    return _vectorized_chr(
        np.sum(array_4x2 * _BRAILLE_ENUM, axis=(2, 3), initial=0x2800)
    )


def binary_to_box(array_2x2: NDArray[np.bool_ | np.uint]) -> NDArray[np.dtype("<U1")]:
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
    return _vectorized_box_map(np.sum(array_2x2 * _BOX_ENUM, axis=(2, 3)))
