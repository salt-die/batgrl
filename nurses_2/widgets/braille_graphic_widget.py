import numpy as np

from .widget import Widget

_TO_BIN = np.array(
    [
        [ 1,   8],
        [ 2,  16],
        [ 4,  32],
        [64, 128],
    ],
    dtype=np.uint8,
)

vectorized_chr = np.vectorize(chr)

def texture_to_braille(arr):
    """
    Convert a `(m, n)`-shaped texture array to a `(m // 4, n // 2)`-shaped
    array of braille characters.

    Example
    -------
           In            -->           Out
    [0 1 0 1 1 0 1 0]           ['⢸' '⠺' '⡅' '⢵']
    [0 1 1 1 0 0 0 1]           ['⡄' '⡾' '⢜' '⠠']
    [0 1 0 1 1 0 1 1]
    [0 1 0 0 1 0 0 1]
    [0 0 0 1 0 1 0 0]
    [0 0 1 1 0 1 0 0]
    [1 0 1 1 1 0 0 1]
    [1 0 1 0 0 1 0 0]
    """
    h, w = arr.shape
    sectioned = np.rollaxis(arr.reshape(h // 4, w // 2, 4, 2), 2, 1)

    ords = np.sum(
        sectioned * _TO_BIN,
        axis=(2, 3),
        initial=0x2800,  # First braille ord
        dtype=np.uint16
    )

    return vectorized_chr(ords)


# Method to update canvas with texture?
# Option to auto-update on render? (potentially slow)
class BrailleGraphicWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        h, w = self.size
        self.texture = np.zeros((4 * h, 2 * w), dtype=np.uint8)

        raise NotImplementedError
