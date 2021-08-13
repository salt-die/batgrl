import cv2
import numpy as np
from numpy.linalg import norm

from .face_colors import FACE_COLORS, SELECTED_COLORS
from . import rotation


class Camera:
    __slots__ = (
        "translation",
        "plane",
        "camera_matrix",
        # Buffers
        "_POINTS_2D_INT_BUFFER",
        "_NORMALS_BUFFER",
        "_POS_BUFFER",
    )

    INITIAL_Z_DISTANCE = 6.0

    INITIAL_X_ANGLE = np.pi / 6
    INITIAL_Y_ANGLE = np.pi / 6
    INITIAL_Z_ANGLE = 0.0

    CX = 0.0  # x-center of image
    CY = 0.0  # y-center of image
    FX = 1.0  # x-focal length
    FY = 1.0  # y-focal length

    DISTORTION_COEF = np.array([0.0, 0.0, 0.0, 0.0])

    def __init__(self):
        self._POINTS_2D_INT_BUFFER = np.zeros((2, 2, 2, 2), dtype=int)
        self._NORMALS_BUFFER = np.zeros(6, dtype=float)
        self._POS_BUFFER = np.zeros(3, dtype=float)

        self.translation = np.array([0.0, 0.0, self.INITIAL_Z_DISTANCE])

        self.plane = plane = rotation.x(self.INITIAL_X_ANGLE).copy()
        np.matmul(plane, rotation.y(self.INITIAL_Y_ANGLE), out=plane)
        np.matmul(plane, rotation.z(self.INITIAL_Z_ANGLE), out=plane)

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
        """
        Position of camera in world coordinates.
        """
        # General camera position is calculated as
        # `-self.plane.T @ self.translation`, but
        # translation for camera is [0, 0, Z],
        # so simplification is possible.
        return np.multiply(self.plane[2], -self.z_distance, out=self._POS_BUFFER)

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
        np.matmul(self.plane, rotation.x(theta), out=self.plane)

    def rotate_y(self, theta):
        np.matmul(self.plane, rotation.y(theta), out=self.plane)

    def rotate_z(self, theta):
        np.matmul(self.plane, rotation.z(theta), out=self.plane)

    def render_cube(self, cube, image, aspect_ratio=True):
        """
        Project and render a cube onto an image array.
        """
        h, w, _ = image.shape

        if aspect_ratio:
            if w > h:
                self.focal_x = h / w
                self.focal_y = 1.0
            else:
                self.focal_x = 1.0
                self.focal_y = w / h

        points_2d, _ = cv2.projectPoints(
            cube.vertices.reshape(-1, 3),
            cv2.Rodrigues(self.plane)[0],
            self.translation,
            self.camera_matrix,
            self.DISTORTION_COEF,
        )

        # Translate to center and scale to image:
        points_2d += .5
        points_2d *= w, h

        vertices_2d = self._POINTS_2D_INT_BUFFER
        vertices_2d[:] = points_2d.reshape(2, 2, 2, 2)  # Cast to int

        pos = self.pos
        normals = np.matmul(cube.normals, pos, out=self._NORMALS_BUFFER)

        it = zip(normals, cube.face_pos, cube.faces, SELECTED_COLORS if cube.is_selected else FACE_COLORS)

        faces = [(face_pos, face, color) for normal, face_pos, face, color in it if normal > 0]
        faces = [(norm(face_pos - pos), face, color) for face_pos, face, color in faces]

        # Sort faces by distance to camera.
        faces.sort(key=lambda tup: tup[0], reverse=True)

        for distance, face, color in faces:
                                                               # Darken color by distance #
            cv2.fillConvexPoly(image, vertices_2d[face], color * (7 ** (-distance * .1)))
