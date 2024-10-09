"""
Cython implementation of Wu's Color Quantizer.

Notes
-----
Greedy orthogonal bipartition of RGB space for variance minimization aided
by inclusion-exclusion tricks. For speed no nearest neighbor search is done.

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
    image: NDArray[np.uint8],
) -> tuple[NDArray[np.uint8], NDArray[np.uint8]]:
    """
    Cython implementation of Wu's Color Quantizer.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.uint8]]
        The quantized palette and an array of indices into palette of each pixel in the
        original image. Palette color channels range from 0 to 100 to conform to the
        sixel format.

    Notes
    -----
    Greedy orthogonal bipartition of RGB space for variance minimization aided
    by inclusion-exclusion tricks. For speed no nearest neighbor search is done.

    References
    ----------
    Xiaolin Wu, "Efficient Statistical Computations for Optimal Color Quantization",
    Graphics Gems II, (ed. James Arvo), Academic Press: Boston, 1991.

    `Wu's Implementation <https://gist.github.com/bert/1192520>`_
    """
