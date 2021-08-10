import numpy as np

import rotation


class Camera:
    __slots__ = "widget", "plane",

    Z_POS = -6

    INITIAL_X_ANGLE = np.pi / 6
    INITIAL_Y_ANGLE = np.pi / 6

    _POSITION_BUFFER = np.zeros(3, dtype=np.float16)
    _DIRECTIONS_BUFFER = np.zeros((4, 3), dtype=np.float16)
    _SCALE_BUFFER = np.zeros((1, 4), dtype=np.float16)
    _PROJECTIONS_BUFFER = np.zeros_like(_DIRECTIONS_BUFFER)
    _POINTS_2D = np.zeros((4, 2), dtype=np.float16)

    def __init__(self, widget):
        self.widget = widget
        self.plane = rotation.x(self.INITIAL_X_ANGLE).copy() @ rotation.y(self.INITIAL_Y_ANGLE)

    @property
    def center(self):
        # Note height is not divided by two -- Camera has double the height of parent's canvas.
        return self.widget.width / 2, self.widget.height

    @property
    def pos(self):
        return np.multiply(
            self.plane[:, 2],
            self.Z_POS,
            out=self._POSITION_BUFFER,
        )

    def project_face(self, points):
        """
        Project 4 points in 3d-space to 2d-space.

        `points` should be a (4, 3)-shaped np.array.
        """
        pos = self.pos
        plane = self.plane
        xy, z = plane[:, :2], plane[:, 2]

        directions = np.subtract(points, pos, out=self._DIRECTIONS_BUFFER)

        scale = np.matmul(directions, z, out=self._SCALE_BUFFER)
        projections = np.divide(directions, scale.T, out=self._PROJECTIONS_BUFFER)
        np.add(projections, pos, out=projections)

        points2d = np.matmul(projections, xy, out=self._POINTS_2D)

        # Adjust for screen coordinates
        points2d[:, 0] = 1 + points2d[:, 0]
        points2d[:, 1] = 1 - points2d[:, 1]
        points2d *= self.center
        return points2d
