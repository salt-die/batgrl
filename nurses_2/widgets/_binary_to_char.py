"""
Binary to character array converters.
"""
import numpy as np

_BRAILLE_ENUM = np.array(    [
    [ 1,   8],
    [ 2,  16],
    [ 4,  32],
    [64, 128],
])
_BOX_ENUM = np.array([
    [ 1, 4],
    [ 2, 8],
])

vectorized_chr = np.vectorize(chr)
"""Vectorized `chr`."""

vectorized_box_map = np.vectorize(" ▘▖▌▝▀▞▛▗▚▄▙▐▜▟█".__getitem__)
"""Vectorized box enum to box char."""

def binary_to_braille(array_4x2):
    """
    Convert a (h, w, 4, 2)-shaped binary array into
    a (h, w) array of braille unicode characters.
    """
    return vectorized_chr(
        np.sum(
            array_4x2 * _BRAILLE_ENUM,
            axis=(2, 3),
            initial=0x2800,  # first braille ord
        )
    )

def binary_to_box(array_2x2):
    """
    Convert a (h, w, 2, 2)-shaped binary array into
    a (h, w) array of box unicode characters.
    """
    return vectorized_box_map(
        np.sum(array_2x2 * _BOX_ENUM, axis=(2, 3))
    )
