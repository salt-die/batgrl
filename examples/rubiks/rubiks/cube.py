import numpy as np


class Cube:
    """
    A 1 x 1 x 1 cube.
    """
    __slots__ = "pos", "vertices", "normals",

    BASE = np.array(
        [
            [
                [-.5,  .5,  .5],
                [ .5,  .5,  .5],
                [ .5, -.5,  .5],
                [-.5, -.5,  .5],
            ],
            [
                [-.5,  .5, -.5],
                [ .5,  .5, -.5],
                [ .5, -.5, -.5],
                [-.5, -.5, -.5],
            ],
        ],
        dtype=np.float16,
    )

    def __init__(self, pos):
        self.pos = pos

        self.vertices = self.BASE + pos

        i = np.identity(3, dtype=np.float16)
        self.normals = np.stack((i, -i))

    def __matmul__(self, r):
        self.pos @= r
        self.vertices @= r
        self.normals @= r
