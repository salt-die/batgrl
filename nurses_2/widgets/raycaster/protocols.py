"""
Protocols for :class:`nurses_2.widgets.raycaster.Raycaster`.
"""
from typing import Protocol, Literal

import numpy as np


class Map(Protocol):
    """
    Map with non-zero entries indicating walls.

    Notes
    -----
    Wall value `n` will have nth texture in raycaster's texture array, e.g., `wall_textures[n - 1]`.
    """
    ndim: Literal[2]

    def __getitem__(self, y, x):
        """
        Supports numpy indexing. Returns a non-negative integer.
        """


class Camera(Protocol):
    """
    A camera view.

    Notes
    -----
    The renderer expects both `pos` and `plane` be numpy arrays with dtype
    `float` and shapes (2,) and (2, 2) respectively.
    """
    pos: np.ndarray  # shape: (2,), dtype: float
    plane: np.ndarray  # shape: (2, 2), dtype: float


class Texture(Protocol):
    """
    A texture. Typically a np.ndarray.

    Notes
    -----
    This protocol is provided to allow for, say, animated textures. The raycaster
    will function as long as `shape` and `__getitem__` work as expected.
    """
    shape: tuple[int, int, Literal[4]]  # (height, width, rgba)

    def __getitem__(self, key):
        """
        Supports numpy indexing. Return arrays or views with dtype `np.uint8`.
        """
