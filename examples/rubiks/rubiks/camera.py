import numpy as np

import rotation


class Camera:
    __slots__ = "plane",

    Z_POS = -6

    INITIAL_X_ANGLE = np.pi / 6
    INITIAL_Y_ANGLE = np.pi / 6

    _POSITION_BUFFER = np.zeros(3, dtype=np.float16)
    _DIRECTION_BUFFER = np.zeros_like(_POSITION_BUFFER)
    _PROJECTION_BUFFER = np.zeros_like(_POSITION_BUFFER)
    _PROJECT_2D = np.zeros(2, dtype=np.float16)

    def __init__(self):
        self.plane = rotation.x(self.INITIAL_X_ANGLE).copy() @ rotation.y(self.INITIAL_Y_ANGLE)

    @property
    def pos(self):
        return np.multiply(
            self.plane[:, 2],
            self.Z_POS,
            out=self._POSITION_BUFFER,
        )

    def project(self, point):
        pos = self.pos
        plane = self.plane
        xy, z = plane[:, :2], plane[:, 2]

        direction = np.subtract(point, pos, out=self._DIRECTION_BUFFER)

        # 1 / (z @ direction) * direction + pos
        stretch = z @ direction
        projection = np.divide(direction, stretch, out=self._PROJECTION_BUFFER)
        np.add(projection, pos, out=projection)

        return np.matmul(projection, xy, out=self._PROJECT_2D)
