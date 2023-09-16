"""
Protocols for :class:`nurses_2.widgets.raycaster.Raycaster`.
"""
from typing import Literal, Protocol

import numpy as np
from numpy.typing import NDArray


class Map(Protocol):
    """
    Map with non-zero entries indicating walls.

    Notes
    -----
    Wall value `n` will have nth texture in raycaster's texture array, e.g.,
    `wall_textures[n - 1]`.
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

    pos: NDArray[np.float64]
    """Position of camera. Array should have shape `(2,)`."""
    plane: NDArray[np.float64]
    """Rotation of camera. Array should have shape `(2, 2)`."""


class Texture(Protocol):
    """
    A texture. Typically a numpy array.

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
