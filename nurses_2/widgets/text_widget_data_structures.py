"""
Data structures for text widgets.
"""
from wcwidth import wcswidth

__all__ = "CanvasView",

RESET = "\x1b[0m"
BOLD = "\x1b[1m"
ITALIC = "\x1b[3m"
UNDERLINE = "\x1b[4m"
STRIKETHROUGH = "\x1b[9m"
STYLE_ANSI = BOLD, ITALIC, UNDERLINE, STRIKETHROUGH


class CanvasView:
    """
    A wrapper around a :class:`numpy.ndarray` with a convenient :meth:`add_text` method.

    One-dimensional views will have an extra axis pre-pended to make them two-dimensional.
    E.g., a view with shape `(m,)` will be re-shaped to `(1, m)` so that
    the `row` and `column` parameters of `add_text` make sense.

    Methods
    -------
    add_text:
        Add text to the underlying canvas.
    """
    __slots__ = "canvas",

    def __init__(self, canvas):
        if canvas.ndim == 1:
            canvas = canvas[None]

        self.canvas = canvas

    def __getattr__(self, attr):
        return getattr(self.canvas, attr)

    def __getitem__(self, key):
        return type(self)(self.canvas[key])

    def __setitem__(self, key, value):
        self.canvas[key] = value

    def add_text(
        self,
        text,
        row=0,
        column=0,
        *,
        bold=False,
        italic=False,
        underline=False,
        strikethrough=False,
    ):
        """
        Add text to the canvas.

        Parameters
        ----------
        text : str
            Text to add to canvas.
        row : int | tuple[int, ...] | slice, default: 0
            Row or rows to which text is added.
        column : int, default: 0
            The first column to which text is added.
        bold : bool, default: False
            Whether text is bold.
        italic : bool, default: False
            Whether text is italic.
        underline : bool, default: False
            Whether text is underlined.
        strikethrough : bool, default: False
            Whether text is strikethrough.

        Notes
        -----
        Text is meant to be a single line of text. Text is not wrapped if it is too long, instead
        index error is raised.
        """
        canvas = self.canvas
        columns = canvas.shape[1]

        is_style = bold, italic, underline, strikethrough
        PREPEND = "".join(ansi for style, ansi in zip(is_style, STYLE_ANSI) if style)
        POSTPEND = RESET if PREPEND else ""

        if column < 0:
            column += columns

        i = 0
        for letter in text:
            if column + i >= columns:
                break

            match wcswidth(letter):
                case 1:
                    canvas[row, column + i] = f"{PREPEND}{letter}{POSTPEND}"
                    i += 1
                case 2:
                    canvas[row, column + i] = f"{PREPEND}{letter}{POSTPEND}"
                    if column + i + 1 < columns:
                        canvas[row, column + i + 1] = chr(0x200B)  # Zero-width space
                    i += 2
