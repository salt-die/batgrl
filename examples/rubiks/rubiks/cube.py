import asyncio
import numpy as np


class Cube:
    """
    A 1 x 1 x 1 cube.
    """
    __slots__ = "pos", "vertices", "normals", "is_selected",

    BASE = np.full((2, 2, 2, 3), .45)  # Each axis represents two faces of the cube

    BASE[..., 0, 0]  *= -1  # Left of cube, x-coordinates are negative
    BASE[:, 1, :, 1] *= -1  # Bottom of cube, y-coordinates are negative
    BASE[1, ..., 2]  *= -1  # Back of cube, z-coordinates are negative

    NORMALS = np.array(
        [
            [ 0,  0,  1], # Front
            [ 0,  0, -1], # Back
            [ 0,  1,  0], # Top
            [ 0, -1,  0], # Bottom
            [-1,  0,  0], # Left
            [ 1,  0 , 0], # Right
        ],
        dtype=float,
    )

    def __init__(self, pos):
        self.pos = np.array(pos, dtype=float)
        self.vertices = self.BASE + pos
        self.normals = self.NORMALS.copy()
        self.is_selected = False

    def __matmul__(self, r):
        np.matmul(self.pos, r, out=self.pos)
        np.matmul(self.vertices, r, out=self.vertices)
        np.matmul(self.normals, r, out=self.normals)

    @property
    def faces(self):
        """
        Return indices that represent the faces of the cube, i.e.,
            ```
            self.vertices[faces[0]]
            ```
        is the front face.

        Faces are returned in (front, back, top, bottom, right, left)-order.

        Vertices on one axis are swapped so that all vertices are in clockwise-order.
        This is required for the `fillConvexPoly` function in `cv2`.
        """
        return (
                           #  Normal  #  # Swapped  #
            (           0, (0, 0, 1, 1), (0, 1, 1, 0)),  # Front
            (           1, (0, 0, 1, 1), (0, 1, 1, 0)),  # Back
             # Swapped  #                #  Normal  #
            ((0, 1, 1, 0),            0, (0, 0, 1, 1)),  # Top
            ((0, 1, 1, 0),            1, (0, 0, 1, 1)),  # Bottom
             #  Normal  #  # Swapped  #
            ((0, 0, 1, 1), (0, 1, 1, 0),            0),  # Left
            ((0, 0, 1, 1), (0, 1, 1, 0),            1),  # Right
        )
