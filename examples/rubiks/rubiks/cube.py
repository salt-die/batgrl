import numpy as np

_EMPTY_SLICE = slice(None)


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

    NORMALS = np.array(
        [
            [ 0,  0, -1], # Front
            [ 0,  0,  1], # Back
            [ 0,  1,  0], # Top
            [ 0, -1,  0], # Bottom
            [-1,  0,  0], # Left
            [ 1,  0 , 0], # Right
        ]
    )

    def __init__(self, pos):
        self.pos = pos
        self.vertices = self.BASE + pos
        self.normals = self.NORMALS.copy()

    def __matmul__(self, r):
        np.matmult(self.pos, r, out=self.pos)
        np.matmult(self.vertices, r, out=self.vertices)
        np.matmult(self.normals, r, out=self.normals)

    @property
    def front(self):
        return 0

    @property
    def back(self):
        return 1

    @property
    def top(self):
        return _EMPTY_SLICE, 0

    @property
    def bottom(self):
        return _EMPTY_SLICE, 1

    @property
    def left(self):
        return _EMPTY_SLICE, _EMPTY_SLICE, 0

    @property
    def right(self):
        return _EMPTY_SLICE, _EMPTY_SLICE, 1

    @property
    def faces(self):
        yield from (
            self.front,
            self.back,
            self.top,
            self.bottom,
            self.left,
            self.right,
        )
