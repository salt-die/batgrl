import numpy as np

from .widget import Widget

vectorized_chr = np.vectorize(chr)

def texture_to_braille(arr):
    """
    Convert a texture array to array of braille characters.

    Example
    -------
           In            -->           Out
    [0 1 0 1 1 0 1 0]           ['⢸' '⠺' '⡅' '⢵']
    [0 1 1 1 0 0 0 1]           ['⡄' '⡾' '⢜' '⠠']
    [0 1 0 1 1 0 1 1]           ['⡺' '⣟' '⠪' '⢻']
    [0 1 0 0 1 0 0 1]           ['⢷' '⢡' '⢛' '⢾']
    [0 0 0 1 0 1 0 0]
    [0 0 1 1 0 1 0 0]
    [1 0 1 1 1 0 0 1]
    [1 0 1 0 0 1 0 0]
    [0 1 1 1 0 1 1 1]
    [1 1 1 1 1 0 1 1]
    [0 1 1 0 0 1 0 1]
    [1 0 1 1 0 0 0 1]
    [1 0 1 0 1 1 0 1]
    [1 1 0 0 1 1 1 1]
    [1 1 0 1 0 0 1 1]
    [0 1 0 1 0 1 0 1]
    """
    BRAILLE_ORD = 0x2800

    h, w = arr.shape
    ords = np.full((h // 4, w // 2), BRAILLE_ORD, dtype=np.uint16)
    _buffer = np.zeros_like(ords)

    slices = (
        arr[ ::4,  ::2],
        arr[1::4,  ::2],
        arr[2::4,  ::2],
        arr[ ::4, 1::2],
        arr[1::4, 1::2],
        arr[2::4, 1::2],
        arr[3::4,  ::2],
        arr[3::4, 1::2],
    )

    for i, s in enumerate(slices):
        ords += np.multiply(s, 2**i, out=_buffer)

    return vectorized_chr(ords)


# Method to update canvas with texture?
# Option to auto-update on render? (potentially slow)
class BrailleGraphicWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        h, w = self.size
        self.texture = np.zeros((4 * h, 2 * w), dtype=np.uint8)

        raise NotImplementedError
