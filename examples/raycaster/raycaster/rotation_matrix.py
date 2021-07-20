import numpy as np

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
