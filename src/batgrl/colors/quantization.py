"""Functions for quantizing RGB textures."""

import cv2
import numpy as np
from numpy.typing import NDArray


def kmeans_quantization(
    rgb: NDArray[np.uint8], n: int = 256
) -> tuple[NDArray[np.int32], NDArray[np.uint8]]:
    """
    Quantize a texture array into ``n`` colors.

    Parameters
    ----------
    rgb : NDArray[np.uint8]
        The texture to quantize.
    n : int, default: 256
        The number of colors in quantization.

    Returns
    -------
    tuple[NDArray[np.int32], NDArray[np.uint8]]
        The quantized palette and an array of indices into palette of each pixel in
        original texture.
    """
    h, w, depth = rgb.shape
    _, labels, centers = cv2.kmeans(
        rgb.reshape(-1, depth).astype(np.float32),
        n,
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        10,
        cv2.KMEANS_PP_CENTERS,
    )
    return centers.astype(np.uint8), labels.reshape(h, w)
