"""Functions for quantizing RGB textures."""

from typing import Final

import cv2
import numpy as np
from numpy.typing import NDArray

PALETTE_256: Final[NDArray[np.uint8]] = np.array(
    np.meshgrid(
        np.linspace(0, 255, 8, True, dtype=np.uint8),
        np.linspace(0, 255, 8, True, dtype=np.uint8),
        np.linspace(0, 255, 4, True, dtype=np.uint8),
    )
).T.reshape(-1, 3)
"""Palette used for ``uint8_quantization``."""


def kmeans_quantization(
    texture: NDArray[np.uint8],
) -> tuple[NDArray[np.int32], NDArray[np.uint8]]:
    """
    Quantize a texture array using kmeans clustering.

    Parameters
    ----------
    texture : NDArray[np.uint8]
        The texture to quantize.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.int32]]
        The quantized palette and an array of indices into palette of each pixel in
        original texture.
    """
    h, w, depth = texture.shape
    flat = texture.reshape(-1, depth)
    _, labels, centers = cv2.kmeans(
        flat.astype(np.float32),
        min(256, np.unique(flat, axis=0).shape[0]),
        None,
        (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0),
        10,
        cv2.KMEANS_PP_CENTERS,
    )
    return centers.astype(np.uint8), labels.reshape(h, w)


def uint8_quantization(
    texture: NDArray[np.uint8],
) -> tuple[NDArray[np.int32], NDArray[np.uint8]]:
    """
    Quantize a texture array using most significant bits.

    Parameters
    ----------
    texture : NDArray[np.uint8]
        The texture to quantize.

    Returns
    -------
    tuple[NDArray[np.uint8], NDArray[np.uint8]]
        The quantized palette and an array of indices into palette of each pixel in
        original texture.
    """
    bits = texture[..., :3] & 0b11100000
    bits[..., 1] >>= 3
    bits[..., 2] >>= 6
    return PALETTE_256, bits.sum(axis=-1, dtype=np.uint8)
