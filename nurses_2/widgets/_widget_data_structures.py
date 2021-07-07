from typing import NamedTuple


class CanvasView:
    """
    A wrapper around an `numpy` `ndarray` that has `Widget`'s `add_text` method.

    Warning
    -------
    1-dimensional slices will return 2-d views with a new axis inserted before the original axis.
    (This is to ensure that the `add_text` method doesn't raise an IndexError.)
    """
    def __init__(self, canvas):
        if len(canvas.shape) == 1:
            canvas = canvas[None]  # Ensure array is 2-dimensional

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
