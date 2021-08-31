from typing import NamedTuple


class CanvasView:
    """
    A wrapper around a `numpy` `ndarray` view with `Widget`'s `add_text` method.

    Notes
    -----
    One-dimensional views will have an extra axis pre-pended to make them two-dimensional.
    E.g., rows and columns with shape (m,) will be re-shaped to (1, m) so that
    the `add_text` `row` and `column` parameters make sense.
    """
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

    def add_text(self, text, row=0, column=0):
        """
        Add text to the canvas.

        Parameters
        ----------
        text: str
            Text to add to canvas.
        row: int | tuple[int, ...] | slice
            Row or rows to which text is added. This will be passed as-is as the first argument
            to `numpy`'s `ndarray.__getitem__`.
        column: int
            The first column to which text is added.
        """
        if column < 0:
            column += self.canvas.shape[1]

        self.canvas[row, column:column + len(text)] = tuple(text)


class Rect(NamedTuple):
    top: int
    left: int
    bottom: int
    right: int
    height: int
    width: int
