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
    _NORMALS_BUFFER       = np.zeros(6, dtype=np.float16)

    def __init__(self):
        self.plane = rotation.x(self.INITIAL_X_ANGLE).copy() @ rotation.y(self.INITIAL_Y_ANGLE)
        self.plane[:, 2] *= -1

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

        directions = np.subtract(cube.vertices, pos, out=self._DIRECTIONS_BUFFER)

        scale = np.matmul(directions, z, out=self._SCALE_BUFFER)

        projections = np.divide(directions, scale.T, out=self._PROJECTIONS_BUFFER)
        np.add(projections, pos, out=projections)

        points2d = np.matmul(projections, xy, out=self._POINTS_2D_BUFFER)
        points2d[:, 0] += 1
        points2d[:, 1] = 1 - points2d[:, 1]
        h, w, _ = image.shape
        points2d *= w / 2, h / 2

        normals = np.matmul(cube.normals, pos, out=self._NORMALS_BUFFER)

        for normal, face, color in zip(normals, cube.faces, FACE_COLORS):
            if normal > 0:
                pts = cv2.convexHull(points2d[face].reshape(-1, 2).astype(int))  # Re-order the points; TODO: optimize slices instead
                cv2.fillConvexPoly(image, pts, color[::-1] if TESTING else color)


if TESTING:
    from cube import Cube

    image = np.zeros((200, 200, 3), dtype=np.uint8)

    cubes = [
        Cube(np.array([3, 3, 0])),
        Cube(np.array([2, 2, 1])),
        Cube(np.array([1, 3, 0])),
    ]

    cam = Camera()

    for cube in cubes:
        cam.render_cube(cube, image)

    cv2.imwrite('test.png', image)
