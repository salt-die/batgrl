"""
Data structures for text widgets.
"""
import numpy as np
from wcwidth import wcswidth, wcwidth

__all__ = "add_text",

RESET = "\x1b[0m"
STYLE_ANSI = BOLD, ITALIC, UNDERLINE, STRIKETHROUGH = "\x1b[1m", "\x1b[3m", "\x1b[4m", "\x1b[9m"

def add_text(
    canvas: np.ndarray[object],
    text: str,
    *,
    bold: bool=False,
    italic: bool=False,
    underline: bool=False,
    strikethrough: bool=False,
    truncate_text: bool=False,
):
    """
    Add multiline text to a ``numpy.ndarray`` or view.

    Text is added starting at first index in canvas. Every new line is added on a new row.

    Parameters
    ----------
    canvas : numpy.ndarray[object]
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
        For text that doesn't fit on canvas, truncate text if true else raise an ``IndexError``.
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

    styles = bold, italic, underline, strikethrough
    PREPEND = "".join(ansi for style, ansi in zip(styles, STYLE_ANSI) if style)
    POSTPEND = RESET if PREPEND else ""

    for text_line, canvas_line in zip(text_lines, canvas):
        i = 0
        for letter in text_line:
            if i >= columns:
                break

            canvas_line[i] = f"{PREPEND}{letter}{POSTPEND}"
            i += (width := wcwidth(letter))
            if width == 2 and i <= columns:
                canvas_line[i - 1] = chr(0x200B)  # Zero-width space
