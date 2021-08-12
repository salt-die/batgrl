import asyncio
from itertools import product

import numpy as np
import cv2

from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors.grabbable_behavior import GrabbableBehavior
from nurses_2.colors import BLACK

from .camera import Camera
from .cube import Cube
from . import rotation

ROTATION_FRAMES = 15


class RubiksCube(GrabbableBehavior, Widget):
    """
    A 3-dimensional Rubik's Cube.
    """
    def __init__(
        self,
        *args,
        aspect_ratio=True,
        background_color=BLACK,
        default_char="▀",
        **kwargs
    ):
        super().__init__(*args, default_char=default_char, **kwargs)

        self.aspect_ratio = aspect_ratio
        self.background_color = background_color

        self.camera = Camera()
        self.cubes = np.array(
            [
                Cube(np.array(position))
                for position in product((-1, 0, 1), (1, 0, -1), (1, 0, -1))
            ],
            dtype=object,
        ).reshape(3, 3, 3)

        self._selected_row = self._selected_axis = 0
        self.selected_axis = 0

        self.resize(self.dim)

        self._rotate_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def _unselect(self):
        for cube in self.selected_cubes:
            cube.is_selected = False

    def _select(self):
        for cube in self.selected_cubes:
            cube.is_selected = True

    @property
    def selected_row(self):
        return self._selected_row

    @selected_row.setter
    def selected_row(self, row):
        self._unselect()
        self._selected_row = row % 3
        self._select()

    @property
    def selected_axis(self):
        return self._selected_axis

    @selected_axis.setter
    def selected_axis(self, axis):
        self._unselect()
        self._selected_axis = axis % 3
        self._select()

    @property
    def selected_indices(self):
        return (
            *((slice(None), ) * self.selected_axis),
            self._selected_row,
        )

    @property
    def selected_cubes(self):
        return self.cubes[self.selected_indices].flatten()

    def resize(self, dim):
        super().resize(dim)

        self._colors_buffer = np.zeros((2 * self.height, self.width, 3), dtype=np.uint8)
        self._update_colors()

    def _update_colors(self):
        """
        Repaint the cube.
        """
        colors_buffer = self._colors_buffer
        colors_buffer[:, :] = self.background_color

        cam = self.camera
        cubes = list(self.cubes.flatten())
        cubes.sort(key=lambda cube: np.linalg.norm(cam.pos - cube.pos), reverse=True)

        for cube in cubes:
            cam.render_cube(cube, colors_buffer, self.aspect_ratio)

        np.concatenate((colors_buffer[::2], colors_buffer[1::2]), axis=-1, out=self.colors)

    def on_press(self, key_press):
        if key_press.key.lower() == "r":
            if not self._rotate_task.done():
                return True

            clockwise = int(key_press.key.isupper())

            theta = np.pi / 2 / ROTATION_FRAMES
            r = getattr(rotation, 'xzy'[self.selected_axis])(theta * (1 if clockwise else -1))

            self._rotate_task = asyncio.create_task(self._rotate(r, list(self.selected_cubes)))

            cubes = self.cubes
            selected_indices = self.selected_indices

            cubes[selected_indices] = np.rot90(
                cubes[selected_indices],
                clockwise,
            )

            return True

        if key_press.key == "up":
            self.selected_row += 1
        elif key_press.key == "down":
            self.selected_row -= 1
        elif key_press.key == "left":
            self.selected_axis -= 1
        elif key_press.key == "right":
            self.selected_axis += 1
        else:
            return False

        self._update_colors()
        return True

    async def _rotate(self, r, cubes):
        for _ in range(ROTATION_FRAMES):
            for cube in cubes:
                cube @ r

            self._update_colors()

            await asyncio.sleep(.08)
