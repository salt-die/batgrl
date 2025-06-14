"""Tools for text."""

from enum import IntFlag
from typing import Final

import numpy as np
from ugrapheme import grapheme_iter
from uwcwidth import wcswidth

from ._batgrl_markdown import find_md_tokens
from .array_types import Cell, Cell0D, Cell1D, Cell2D, cell_dtype
from .colors import BLACK, WHITE, Color
from .geometry import Size
from .logging import get_logger

__all__ = [
    "Cell",
    "Cell0D",
    "Cell1D",
    "Cell2D",
    "Style",
    "add_text",
    "cell_dtype",
    "is_word_char",
    "new_cell",
    "smooth_horizontal_bar",
    "smooth_vertical_bar",
]

EGC_BASE: Final = 0x180000
"""A bit flag to mark egcs in canvas arrays. Must be greater than `sys.maxunicode`."""
EGC_POOL: list[str] = []
"""
Storage for extended grapheme clusters.

If `ord_` is an ord in a canvas array and `ord_ & EGC_BASE` is non-zero, then
`ord_ - EGC_BASE` is an index into `EGC_POOL`. In this way, we can use the uint32 "ord"
field in canvas arrays to store both codepoints and egcs.
"""
EGCS: dict[str, int] = {}
"""Extended grapheme clusters currently stored in EGC_POOL and their index."""
VERTICAL_BLOCKS: Final = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS: Final = " ▏▎▍▌▋▊▉█"

logger = get_logger(__name__)


class Style(IntFlag):
    """The graphic rendition parameters of a terminal cell."""

    # ! Don't use auto() as these must match the definitions in _rendering.pyx.
    DEFAULT = 0
    BOLD = 0b1
    ITALIC = 0b10
    UNDERLINE = 0b100
    STRIKETHROUGH = 0b1000
    OVERLINE = 0b10000
    REVERSE = 0b100000


def egc_ord(text: str) -> int:
    """
    Return either a unicode codepoint or an index into the egc pool for the first
    extended grapheme cluster in ``text``.

    Parameters
    ----------
    text : str
        An extended grapheme cluster.

    Returns
    -------
    int
        A unicode codepoint or an index into ``EGC_POOL``.

    See Also
    --------
    egc_chr
    """
    if len(text) == 0:
        return 0

    egc = next(grapheme_iter(text))
    if len(egc) == 1:
        return ord(egc)

    if egc not in EGCS:
        # FIXME: Unbounded growth
        logger.debug(f"EGC Added: {egc} {[ord(i) for i in egc]}")
        EGCS[egc] = len(EGC_POOL)
        EGC_POOL.append(egc)
    return EGCS[egc] | EGC_BASE


def egc_chr(ord: int) -> str:
    """
    Return the extended grapheme cluster represented by ``ord``.

    Parameters
    ----------
    ord : int
        The ord of the extended grapheme cluster.

    Returns
    -------
    str
        The extended grapheme cluster represented by ``ord``.

    See Also
    --------
    egc_ord
    """
    return EGC_POOL[ord - EGC_BASE] if ord & EGC_BASE else chr(ord)


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


def new_cell(
    ord: int = 0x20,
    style: Style = Style.DEFAULT,
    fg_color: Color = WHITE,
    bg_color: Color = BLACK,
) -> Cell0D:
    """
    Create a 0-dimensional ``cell_dtype`` array.

    A ``cell_dtype`` is a structured array type that represents a single cell in a
    terminal.

    Parameters
    ----------
    ord : int, default: 0x20
        The cell's character's ord.
    style : Style, Style.DEFAULT
        The style (bold, italic, etc.) of the cell.
    fg_color : Color, default: WHITE
        Foreground color of cell.
    bg_color : Color, default: BLACK
        Background color of cell.

    Returns
    -------
    Cell0D
        A 0-dimensional ``cell_dtype`` array.
    """
    return np.array((ord, style, fg_color, bg_color), dtype=cell_dtype)


def _parse_batgrl_md(text: str) -> tuple[Size, list[list[Cell0D]]]:
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
    tuple[Size, list[list[Cell0D]]]
        Minimum canvas size to fit text and a list of lines of styled characters.
    """
    NO_CHAR = new_cell(ord=0)
    matches, escapes = find_md_tokens(text)
    cells = [
        new_cell(ord=egc_ord(egc))[["ord", "style"]] for egc in grapheme_iter(text)
    ]
    for before, start, end, after, style in matches:
        cells[start - before : start] = [NO_CHAR] * before
        cells[end : end + after] = [NO_CHAR] * after
        for i in range(start, end):
            cells[i]["style"] |= getattr(Style, style.upper())

    for i in escapes:
        cells[i] = NO_CHAR

    lines = []
    line = []
    line_width = max_width = 0

    for cell in cells:
        ord_ = cell["ord"].item()
        if ord_ == 0:
            continue

        if ord_ == 0xA:
            lines.append(line)
            line = []
            if line_width > max_width:
                max_width = line_width
            line_width = 0
        else:
            width = wcswidth(egc_chr(ord_))
            if width > 0:
                line_width += width
                line.append(cell)

    lines.append(line)
    if line_width > max_width:
        max_width = line_width

    return Size(len(lines), max_width), lines


def _text_to_cells(text: str) -> tuple[Size, list[list[Cell0D]]]:
    """
    Convert some text to a list of lists of cells and the minimum canvas size to fit
    them.

    Parameters
    ----------
    text : str
        The text to convert.

    Returns
    -------
    tuple[Size, list[list[Cell0D]]]
        Minimum canvas size to fit text and a list of lists of cells.
    """
    egcs = [list(grapheme_iter(line)) for line in text.split("\n")]
    cells = []
    max_width = 0
    for egc_line in egcs:
        line_width = 0
        cell_line = []
        for egc in egc_line:
            egc_width = wcswidth(egc)
            if egc_width <= 0:
                continue
            cell_line.append(new_cell(ord=egc_ord(egc)))
            line_width += egc_width
        cells.append(cell_line)
        if line_width > max_width:
            max_width = line_width
    return Size(len(cells), max_width), cells


def _write_cells_to_canvas(cells, canvas, fg_color, bg_color) -> None:
    """Write a list of lists of cells to a canvas array."""
    _, columns = canvas.shape
    for cell_line, canvas_line in zip(cells, canvas):
        i = 0
        for cell in cell_line:
            char_width = wcswidth(egc_chr(cell["ord"].item()))
            if char_width < 1:
                continue

            if i + char_width > columns:
                canvas_line[i:]["ord"] = 0x2
                canvas_line[i:]["style"] = 0
                if fg_color is not None:
                    canvas_line[i:]["fg_color"] = fg_color
                if bg_color is not None:
                    canvas_line[i:]["bg_color"] = bg_color
                break

            canvas_line[i]["ord"] = cell["ord"]
            canvas_line[i + 1 : i + char_width]["ord"] = 0
            canvas_line[i : i + char_width]["style"] = cell["style"]

            if fg_color is not None:
                canvas_line[i : i + char_width]["fg_color"] = fg_color
            if bg_color is not None:
                canvas_line[i : i + char_width]["bg_color"] = bg_color

            i += char_width
            if i >= columns:
                break


def add_text(
    canvas: Cell1D | Cell2D,
    text: str,
    *,
    fg_color: Color | None = None,
    bg_color: Color | None = None,
    markdown: bool = False,
    truncate_text: bool = False,
) -> None:
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
    canvas : Cell1D | Cell2D
        A 1- or 2-dimensional view of a ``Cell`` array.
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
    size, cells = _parse_batgrl_md(text) if markdown else _text_to_cells(text)
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape
    if not truncate_text and (size.height > rows or size.width > columns):
        raise IndexError("Text does not fit in canvas.")
    _write_cells_to_canvas(cells, canvas, fg_color, bg_color)


def canvas_as_text(
    canvas: Cell1D | Cell2D, line_widths: list[int] | None = None
) -> str:
    """
    Return a ``Cell`` array as a single multi-line string.

    Parameters
    ----------
    canvas : Cell1D | Cell2D
        The ``Cell`` array to convert.
    line_widths : list[int] | None
        Optionally truncate line ``n`` to have column width ``line_widths[n]``. If
        line_widths[``n``] is greater than the column width of line ``n`` it is ignored.

    Returns
    -------
    str
        The canvas as a multi-line string.
    """
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape
    if line_widths is None:
        line_widths = [columns] * rows
    elif len(line_widths) < rows:
        line_widths = line_widths + [columns] * (rows - len(line_widths))

    text = []
    for row, line_width in zip(canvas, line_widths, strict=True):
        current_line_width = 0
        line = []
        for cell in row:
            char = egc_chr(cell["ord"])
            char_width = wcswidth(char)
            if char_width <= 0:
                continue
            if char_width + current_line_width > line_width:
                break
            current_line_width += char_width
            line.append(char)
        text.append("".join(line))
    return "\n".join(text)


def _smooth_bar(
    blocks: str,
    max_length: int,
    proportion: float,
    offset: float,
) -> tuple[str, ...]:
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
