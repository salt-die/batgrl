import numpy as np


class Cube:
    """
    A 1 x 1 x 1 cube.
    """
    __slots__ = "pos", "vertices", "normals",

    # This array is 2 x 2 x 2 x 3 with each of the first 3 axis representing
    # a face of a cube.
    BASE = np.array(
        [
            [
                [[-.5,  .5,  .5], [ .5,  .5,  .5]],
                [[ .5, -.5,  .5], [-.5, -.5,  .5]],
            ],
            [
                [[-.5,  .5, -.5], [ .5,  .5, -.5]],
                [[ .5, -.5, -.5], [-.5, -.5, -.5]],
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
        np.matmult(self.pos, r, out=self.pos)
        np.matmult(self.vertices, r, out=self.vertices)
        np.matmult(self.normals, r, out=self.normals)

    @property
    def front(self):
        return self.vertices[0]

    @property
    def back(self):
        return self.vertices[1]

    @property
    def top(self):
        return self.vertices[:, 0]

    @property
    def bottom(self):
        return self.vertices[:, 1]

    @property
    def left(self):
        return self.vertices[:, :, 0]

    @property
    def right(self):
        return self.vertices[:, :, 1]
