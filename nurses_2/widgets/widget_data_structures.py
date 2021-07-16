from typing import NamedTuple, Optional


class CanvasView:
    """
    A wrapper around an `numpy` `ndarray` that has `Widget`'s `add_text` method.

    Warning
    -------
    The canvas or canvas view passed to `CanvasView` should be 2-dimensional.
    If a single row or column is needed, add `None` to the `__getitem__` key,
    `my_canvas_view[None, 0, :-1]` or `my_canvas_view[:-1, 0, None]`.
    """
    def __init__(self, canvas):
        assert len(canvas.shape) == 2, f"view has bad shape, {canvas.shape}"
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


class Point(NamedTuple):
    y: int
    x: int


class PosHint(NamedTuple):
    y: float
    x: float


class Size(NamedTuple):
    height: Optional[float]
    width: Optional[float]


class SizeHint(NamedTuple):
    height: Optional[float]
    width: Optional[float]


class Rect(NamedTuple):
    top: int
    left: int
    bottom: int
    right: int
    height: int
    width: int
