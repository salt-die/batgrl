"""
Cython implementation of Wu's Color Quantizer.

Notes
-----
Greedy orthogonal bipartition of RGB space for variance minimization aided by
inclusion-exclusion tricks. For speed, no nearest neighbor search is done.

References
----------
Xiaolin Wu, "Efficient Statistical Computations for Optimal Color Quantization",
Graphics Gems II, (ed. James Arvo), Academic Press: Boston, 1991.

`Wu's Implementation <https://gist.github.com/bert/1192520>`_
"""

import numpy as np
from numpy.typing import NDArray

__all__ = ["median_variance_quantization"]

def median_variance_quantization(
    texture: NDArray[np.uint8], oy: int, ox: int, h: int, w: int
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """
    Cython implementation of Wu's Color Quantizer.

    Parameters
    ----------
    texture : NDArray[np.uint8]
        A RGB or RGBA texture to quantize.
    oy : int
        Y-coordinate of rect in texture to quantize.
    ox : int
        X-coordinate of rect in texture to quantize.
    h : int
        Height of rect in texture to quantize.
    w : int
        Width of rect in texture to quantize.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.uint8]]
        The quantized palette and an array of indices into the palette of each pixel in
        the original texture. Palette color channels range from 0 to 100 to conform to
        the sixel format.

    Notes
    -----
    Greedy orthogonal bipartition of RGB space for variance minimization aided by
    inclusion-exclusion tricks. For speed, no nearest neighbor search is done.

    References
    ----------
    Xiaolin Wu, "Efficient Statistical Computations for Optimal Color Quantization",
    Graphics Gems II, (ed. James Arvo), Academic Press: Boston, 1991.

    `Wu's Implementation <https://gist.github.com/bert/1192520>`_
    """
