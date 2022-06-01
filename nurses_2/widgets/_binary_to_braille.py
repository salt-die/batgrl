"""
Convert a (h, w, 4, 2)-shaped binary array into (h, w) array of
braille unicode characters.
"""
import numpy as np

_TO_DECIMAL = np.array(
    [
        [ 1,   8],
        [ 2,  16],
        [ 4,  32],
        [64, 128],
    ],
)
_TO_DECIMAL.flags.writeable = False

vectorized_chr = np.vectorize(chr)

def binary_to_braille(array_4x2):
    """
    Convert a (h, w, 4, 2)-shaped binary array into
    a (h, w) array of braille unicode characters.
    """
    return vectorized_chr(
        np.sum(
            array_4x2 * _TO_DECIMAL,
            axis=(2, 3),
            initial=0x2800,  # first braille ord
        )
    )
