from typing import Protocol, Tuple

import numpy as np


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
    shape: Tuple[int, int]  # (height, width)

    def __getitem__(self, key):
        """
        Supports numpy indexing.
        """
