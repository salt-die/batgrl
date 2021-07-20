from typing import Protocol

import numpy as np


class Camera(Protocol):
    """
    A camera needs a position `pos` and a plane `plane`.
    The renderer expects both of these to be numpy arrays with
    shapes (2,) and (2, 2) respectively.
    """
    pos: np.ndarray  # shape: (2,), dtype: np.float16
    plane: np.ndarray  # shape: (2, 2), dtype: np.float16


def rotation_matrix(theta):
    """
    Returns a 2-dimensional rotation array of a given angle.

    Notes
    -----
    Matrix multiplication of a rotation matrix and a camera plane will
    rotate the plane.
    """
    x = np.cos(theta)
    y = np.sin(theta)

    return np.array(
        [
            [ x, y],
            [-y, x],
        ],
        dtype=np.float16,
    )
