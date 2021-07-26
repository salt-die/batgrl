from typing import Protocol, Tuple, Literal

import numpy as np


class Map(Protocol):
    """
    Map with non-zero entries indicating walls.

    Notes
    -----
    Wall value `n` will have texture `textures[n - 1]` in raycaster.
    """
    ndim: Literal[2]

    def __getitem__(self, y, x):
        """
        Supports numpy indexing. Return a non-negative integer.
        """


class Camera(Protocol):
    """
    A camera view.

    The renderer expects both `pos` and `plane` be numpy arrays with dtype
    `np.float16` and shapes (2,) and (2, 2) respectively.
    """
    pos: np.ndarray  # shape: (2,), dtype: np.float16
    plane: np.ndarray  # shape: (2, 2), dtype: np.float16


class Texture(Protocol):
    """
    A texture. Typically a np.ndarray.

    Notes
    -----
    This protocol is provided to allow for, say, animated textures. The raycaster
    will function as long as `shape` and `__getitem__` work as expected.
    """
    shape: Tuple[int, int, Literal[3]]  # (height, width, channels)

    def __getitem__(self, key):
        """
        Supports numpy indexing. Return arrays or views with dtype=np.uint8.
        """