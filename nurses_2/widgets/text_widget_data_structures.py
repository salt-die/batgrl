"""
Data structures for text widgets.
"""
from enum import Enum

import numpy as np
from wcwidth import wcswidth, wcwidth

__all__ = "add_text", "Border"

def add_text(
    canvas: np.ndarray,
    text: str,
    *,
    bold: bool=False,
    italic: bool=False,
    underline: bool=False,
    strikethrough: bool=False,
    truncate_text: bool=False,
):
    """
    Add multiline text to a `numpy.ndarray` or view.

    Text is added starting at first index in canvas. Every new line is added on a new row.

    Parameters
    ----------
    canvas : numpy.ndarray
        A 1- or 2-dimensional numpy array of python strings.
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
    truncate_text : bool, default: False
        For text that doesn't fit on canvas, truncate text if true else raise an `IndexError`.
    """
    if canvas.ndim == 1:  # Pre-pend an axis if canvas is one-dimensional.
        canvas = canvas[None]
    rows, columns = canvas.shape

    text_lines = text.splitlines()
    if not truncate_text and (
        len(text_lines) > rows or
        max(map(wcswidth, text_lines), default=0) > columns
    ):
        raise IndexError(f"Text does not fit in canvas.")

    for text_line, canvas_line in zip(text_lines, canvas):
        i = 0
        for letter in text_line:
            if i >= columns:
                break

            width = wcwidth(letter)
            if width == 0:
                continue
            if width == 2 and i + 1 < columns:
                canvas_line[i + 1] = ""

            canvas_line[i] = letter, bold, italic, underline, strikethrough
            i += width


class Border(str, Enum):
    """
    Border styles for :meth:`nurses_2.text_widget.TextWidget.add_border`.

    :class:`Borders` is one of `"light"`, `"heavy"`, `"double"`, `"curved"`,
    `"ascii"`.
    """
    LIGHT = "light"
    HEAVY = "heavy"
    DOUBLE = "double"
    CURVED = "curved"
    ASCII = "ascii"
