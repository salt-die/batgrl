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
    __slots__ = "translation", "rotation", "plane", "camera_matrix"

    INITIAL_Z_DISTANCE = 6.0

    INITIAL_X_ANGLE = np.pi / 6
    INITIAL_Y_ANGLE = np.pi / 6
    INITIAL_Z_ANGLE = 0.0

    CX = 0.0  # x-center of image
    CY = 0.0  # y-center of image
    FX = 1.0  # x-focal length
    FY = 1.0  # y-focal length

    DISTORTION_COEF = np.array([0.0, 0.0, 0.0, 0.0])

    _POSITION_BUFFER = np.zeros(3, dtype=float)
    _POINTS_2D_INT_BUFFER = np.zeros((2, 2, 2, 2), dtype=int)
    _NORMALS_BUFFER = np.zeros(6, dtype=float)

    def __init__(self):
        self.translation = np.array([0.0, 0.0, self.INITIAL_Z_DISTANCE])

        self.rotation = np.array(
            [
                self.INITIAL_X_ANGLE,
                self.INITIAL_Y_ANGLE,
                self.INITIAL_Z_ANGLE,
            ]
        )

        self.plane = plane = np.array([0.0, 0.0, -1.0])
        np.matmul(rotation.x(self.INITIAL_X_ANGLE), plane, out=plane)
        np.matmul(rotation.y(self.INITIAL_Y_ANGLE), plane, out=plane)
        np.matmul(rotation.z(self.INITIAL_Z_ANGLE), plane, out=plane)

        self.camera_matrix = np.array(
            [
                [self.FX,     0.0, self.CX],
                [    0.0, self.FY, self.CY],
                [    0.0,     0.0,     1.0],
            ]
        )

    @property
    def z_distance(self):
        return self.translation[-1]

    @z_distance.setter
    def z_distance(self, distance):
        self.translation[-1] = distance

    @property
    def pos(self):
        return np.multiply(
            self.plane,
            self.z_distance,
            out=self._POSITION_BUFFER,
        )

    @property
    def focal_x(self):
        return self.camera_matrix[0, 0]

    @focal_x.setter
    def focal_x(self, value):
        self.camera_matrix[0, 0] = value

    @property
    def focal_y(self):
        return self.camera_matrix[1, 1]

    @focal_y.setter
    def focal_y(self, value):
        self.camera_matrix[1, 1] = value

    def rotate_x(self, theta):
        self.rotation[0] += theta
        np.matmul(rotation.x(theta), self.plane, out=self.plane)

    def rotate_y(self, theta):
        self.rotation[1] += theta
        np.matmul(rotation.y(theta), self.plane, out=self.plane)

    def rotate_z(self, theta):
        self.rotation[2] += theta
        np.matmul(rotation.z(theta), self.plane, out=self.plane)

    def render_cube(self, cube, image, adjust_aspect=True):
        """
        Project and render a cube onto an image array.
        """
        h, w, _ = image.shape

        if adjust_aspect:
            if w > h:
                self.focal_x = h / w
                self.focal_y = 1.0
            else:
                self.focal_x = 1.0
                self.focal_y = w / h

        points_2d, _ = cv2.projectPoints(
            cube.vertices.reshape(-1, 3),
            self.rotation,
            self.translation,
            self.camera_matrix,
            self.DISTORTION_COEF,
        )

        # Translate to center and scale to image:
        points_2d += .5
        points_2d *= w, h

        vertices_2d = self._POINTS_2D_INT_BUFFER
        vertices_2d[:] = points_2d.reshape(2, 2, 2, 2)  # Cast to int

        normals = np.matmul(cube.normals, self.pos, out=self._NORMALS_BUFFER)

        for normal, face, color in zip(normals, cube.faces, FACE_COLORS):
            if normal > 0:
                cv2.fillConvexPoly(image, vertices_2d[face], color[::-1] if TESTING else color)


if TESTING:
    from itertools import product

    from cube import Cube

    image = np.zeros((150, 300, 3), dtype=np.uint8)

    cubes = [Cube(np.array(position)) for position in product((-1, 0, 1), repeat=3)]
    cam = Camera()
    cubes.sort(key=lambda cube: np.linalg.norm(cam.pos - cube.pos), reverse=True)

    for cube in cubes:
        cam.render_cube(cube, image)

    cv2.imwrite('test.png', image)
