import cv2
import numpy as np

import rotation

TESTING = __name__ == "__main__"

if TESTING:
    # Running as a standalone file
    from face_colors import FACE_COLORS
else:
    # Relative import will work.
    from .face_colors import FACE_COLORS


class Camera:
    __slots__ = "plane",

    Z_DISTANCE = 6

    INITIAL_X_ANGLE = np.pi / 6
    INITIAL_Y_ANGLE = np.pi / 6

    # Buffers
    _POSITION_BUFFER      = np.zeros(3, dtype=np.float16)
    _DIRECTIONS_BUFFER    = np.zeros((2, 2, 2, 3), dtype=np.float16)
    _SCALE_BUFFER         = np.zeros((1, 2, 2, 2), dtype=np.float16)
    _PROJECTIONS_BUFFER   = np.zeros_like(_DIRECTIONS_BUFFER)
    _POINTS_2D_BUFFER     = np.zeros((2, 2, 2, 2), dtype=np.float16)
    _POINTS_2D_INT_BUFFER = np.zeros_like(_POINTS_2D_BUFFER, dtype=int)
    _NORMALS_BUFFER       = np.zeros(6, dtype=np.float16)

    def __init__(self):
        self.plane = rotation.x(self.INITIAL_X_ANGLE).copy() @ rotation.y(self.INITIAL_Y_ANGLE)

    @property
    def pos(self):
        return np.multiply(
            self.plane[:, 2],
            -self.Z_DISTANCE,
            out=self._POSITION_BUFFER,
        )

    def render_cube(self, cube, image):
        """
        Project and render a cube onto an image array.
        """
        pos = self.pos
        plane = self.plane
        xy, z = plane[:, :2], plane[:, 2]

        # Long form of `(cube.vertices - pos) / ((cube.vertices - pos) @ z)`
        # to re-use buffers.
        directions = np.subtract(cube.vertices, pos, out=self._DIRECTIONS_BUFFER)

        scale = np.matmul(directions, z, out=self._SCALE_BUFFER)

        projections = np.divide(directions, scale.T, out=self._PROJECTIONS_BUFFER)
        projections += pos

        points_2d = np.matmul(projections, xy, out=self._POINTS_2D_BUFFER)

        # Translate to center and scale to image:
        h, w, _ = image.shape
        points_2d += .5
        points_2d *= w, h

        vertices_2d = self._POINTS_2D_INT_BUFFER
        vertices_2d[:] = points_2d  # Cast to int

        normals = np.matmul(cube.normals, pos, out=self._NORMALS_BUFFER)

        for normal, face, color in zip(normals, cube.faces, FACE_COLORS):
            if normal > 0:
                cv2.fillConvexPoly(image, vertices_2d[face], color[::-1] if TESTING else color)


if TESTING:
    from itertools import product
    from cube import Cube

    image = np.zeros((200, 200, 3), dtype=np.uint8)

    cubes = [Cube(np.array(position)) for position in product((-1, 0, 1), repeat=3)]
    cam = Camera()
    cubes.sort(key=lambda cube: np.linalg.norm(cam.pos - cube.pos), reverse=True)

    for cube in cubes:
        cam.render_cube(cube, image)

    cv2.imwrite('test.png', image)
