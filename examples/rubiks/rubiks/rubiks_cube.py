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
ROTATION_FRAME_DURATION = .08
QUARTER_TURN = np.pi / 2


class RubiksCube(GrabbableBehavior, Widget):
    """
    A 3-dimensional Rubik's Cube.
    """
    _ROTATION_BUFFER = np.zeros((3, 3), dtype=float)

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
            list(map( Cube, product((-1, 0, 1), (1, 0, -1), (1, 0, -1)) )),
            dtype=object,
        ).reshape(3, 3, 3)

        self._selected_row = self._selected_axis = 0
        self._select()

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
        self._needs_update = True

    def _redraw_cube(self):
        """
        Redraw the cube.
        """
        colors_buffer = self._colors_buffer
        colors_buffer[:, :] = self.background_color

        cam = self.camera
        cubes = list(self.cubes.flatten())
        cubes.sort(key=lambda cube: np.linalg.norm(cam.pos - cube.pos), reverse=True)

        for cube in cubes:
            cam.render_cube(cube, colors_buffer, self.aspect_ratio)

        np.concatenate((colors_buffer[::2], colors_buffer[1::2]), axis=-1, out=self.colors)

        self._needs_update = False

    def on_press(self, key_press):
        if key_press.key.lower() == "r":
            if not self._rotate_task.done():
                return True

            clockwise = int(key_press.key.isupper())
            axis = 'xyz'[self.selected_axis]

            self._rotate_task = asyncio.create_task(
                self._rotate(
                    cubes=list(self.selected_cubes),
                    axis=axis,
                    clockwise=clockwise,
                )
            )

            cubes = self.cubes
            selected_indices = self.selected_indices

            direction = 2 * clockwise - 1
            if axis == 'z':
                direction *= -1

            cubes[selected_indices] = np.rot90(cubes[selected_indices], direction)

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

        self._needs_update = True
        return True

    async def _rotate(self, cubes, axis, clockwise):
        theta = QUARTER_TURN / ROTATION_FRAMES

        if not clockwise:
            theta *= -1

        r = self._ROTATION_BUFFER
        r[:] = getattr(rotation, axis)(theta)

        for _ in range(ROTATION_FRAMES):
            for cube in cubes:
                cube @ r

            self._needs_update = True

            await asyncio.sleep(ROTATION_FRAME_DURATION)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_mouse_pos = mouse_event.position

    def grab_update(self, mouse_event):
        last_y, last_x = self._last_mouse_pos
        y, x = self._last_mouse_pos = mouse_event.position

        # Horizontal movement rotates around vertical axis and vice-versa.
        alpha = np.pi * (last_y - y) / self.height  # vertical movement flipped, world coordinates opposite screen coordinates
        self.camera.rotate_x(alpha)

        beta = np.pi * (x - last_x) / self.width
        self.camera.rotate_y(beta)

        self._needs_update = True

    def render(self, canvas_view, colors_view, rect):
        if self._needs_update:
            self._redraw_cube()

        super().render(canvas_view, colors_view, rect)
