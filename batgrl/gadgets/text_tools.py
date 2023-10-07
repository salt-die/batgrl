"""
Tools for text gadgets.
"""
import numpy as np
from numpy.typing import NDArray
from wcwidth import wcswidth, wcwidth

from .gadget import Char

__all__ = [
    "add_text",
    "binary_to_box",
    "binary_to_braille",
    "smooth_vertical_bar",
    "smooth_horizontal_bar",
]


def add_text(
    canvas: NDArray[Char],
    text: str,
    *,
    bold: bool = False,
    italic: bool = False,
    underline: bool = False,
    strikethrough: bool = False,
    overline: bool = False,
    truncate_text: bool = False,
):
    """
    Add multiple lines of text to a view of a canvas.

    Text is added starting at first index in canvas. Every new line is added on a new
    row.

    Parameters
    ----------
    canvas : NDArray[Char]
        A 1- or 2-dimensional view of a `Text` canvas.
    text : str
        Text to add to canvas.
    bold : bool, default: False
        Whether text is bold.
    italic : bool, default: False
        Whether text is italic.
    underline : bool, default: False
        Whether text is underlined.
    strikethrough : bool, default: False
        Whether text is strikethrough.
    overline : bool, default: False
        Whether text is overlined.
    truncate_text : bool, default: False
        For text that doesn't fit on canvas, truncate text if true else raise an
        `IndexError`.
    """
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape

    text_lines = text.split("\n")
    if not truncate_text and (
        len(text_lines) > rows or max(map(wcswidth, text_lines), default=0) > columns
    ):
        raise IndexError("Text does not fit in canvas.")

    for text_line, canvas_line in zip(text_lines, canvas):
        i = 0
        for letter in text_line:
            if i >= columns:
                break

            width = wcwidth(letter)
            if width == 0:
                continue
            if width == 2 and i + 1 < columns:
                canvas_line[i + 1] = (
                    "",
                    bold,
                    italic,
                    underline,
                    strikethrough,
                    overline,
                )

            canvas_line[i] = letter, bold, italic, underline, strikethrough, overline
            i += width


VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇█"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉█"


def _smooth_bar(
    blocks: str,
    max_length: int,
    proportion: float,
    offset: float,
):
    """
    Create a smooth bar with given blocks.
    """
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
    """
    return _smooth_bar(HORIZONTAL_BLOCKS, max_width, proportion, offset)


_BRAILLE_ENUM = np.array([[1, 8], [2, 16], [4, 32], [64, 128]])
_BOX_ENUM = np.array([[1, 4], [2, 8]])

vectorized_chr = np.vectorize(chr)
"""Vectorized `chr`."""

vectorized_box_map = np.vectorize(" ▘▖▌▝▀▞▛▗▚▄▙▐▜▟█".__getitem__)
"""Vectorized box enum to box char."""


def binary_to_braille(array_4x2):
    """
    Convert a (h, w, 4, 2)-shaped binary array into a (h, w) array of braille unicode
    characters.
    """
    return vectorized_chr(
        np.sum(array_4x2 * _BRAILLE_ENUM, axis=(2, 3), initial=0x2800)
    )


def binary_to_box(array_2x2):
    """
    Convert a (h, w, 2, 2)-shaped binary array into a (h, w) array of box unicode
    characters.
    """
    return vectorized_box_map(np.sum(array_2x2 * _BOX_ENUM, axis=(2, 3)))
