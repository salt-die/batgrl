import asyncio
from itertools import product
from random import randrange

import numpy as np
from numpy.linalg import norm

from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors.grabbable_behavior import GrabbableBehavior

from . import rotation
from .camera import Camera
from .cube import Cube
from .background import Background

ROTATION_FRAMES = 15
ROTATION_FRAME_DURATION = .08
QUARTER_TURN = np.pi / 2


class RubiksCube(GrabbableBehavior, Widget):
    """
    A 3-dimensional Rubik's Cube.
    """
    def __init__(
        self,
        *args,
        aspect_ratio=True,
        default_char="▀",
        **kwargs
    ):
        super().__init__(*args, default_char=default_char, **kwargs)

        self._ROTATION_BUFFER = np.zeros((3, 3), dtype=float)

        self.aspect_ratio = aspect_ratio

        self.camera = Camera()
        self.cubes = np.array(
            list(map( Cube, product((-1, 0, 1), (1, 0, -1), (1, 0, -1)) )),
            dtype=object,
        ).reshape(3, 3, 3)

        self._selected_row = self._selected_axis = 0
        self._select()

        self.background = Background()
        self.add_widget(self.background)
        self.background.play()

        self.resize(self.size)

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

    def resize(self, size):
        super().resize(size)
        self._colors_buffer = np.zeros((2 * self.height, self.width, 3), dtype=np.uint8)

    def on_press(self, key):
        if key.lower() == "r":
            self.rotate_selected_cubes(is_clockwise=key.isupper())
        elif key == "up":
            self.selected_row += 1
        elif key == "down":
            self.selected_row -= 1
        elif key == "left":
            self.selected_axis -= 1
        elif key == "right":
            self.selected_axis += 1
        elif key == "s":
            self.scramble()
        else:
            return False

        return True

    def rotate_selected_cubes(self, is_clockwise, animate=True):
        """
        Rotate the currently selected plane.
        """
        if not self._rotate_task.done():
            return

        axis = "xyz"[self.selected_axis]

        if animate:
            self._rotate_task = asyncio.create_task(
                self._rotate(
                    cubes=list(self.selected_cubes),
                    axis=axis,
                    is_clockwise=is_clockwise,
                )
            )
        else:
            theta = QUARTER_TURN
            if not is_clockwise:
                theta *= -1

            r = getattr(rotation, axis)(theta)

            for cube in self.selected_cubes:
                cube @ r

        cubes = self.cubes
        selected_indices = self.selected_indices

        direction = 2 * is_clockwise - 1
        if axis == "z":
            direction *= -1

        cubes[selected_indices] = np.rot90(cubes[selected_indices], direction)

    def scramble(self, nmoves=20):
        current_row = self._selected_row
        current_axis = self._selected_axis
        self._unselect()

        for _ in range(nmoves):
            self._selected_row = randrange(3)
            self._selected_axis = randrange(3)
            clockwise = randrange(2)

            self.rotate_selected_cubes(clockwise, animate=False)

        self._selected_row = current_row
        self._selected_axis = current_axis
        self._select()

    async def _rotate(self, cubes, axis, is_clockwise):
        theta = QUARTER_TURN / ROTATION_FRAMES

        if not is_clockwise:
            theta *= -1

        r = self._ROTATION_BUFFER
        r[:] = getattr(rotation, axis)(theta)

        for _ in range(ROTATION_FRAMES):
            for cube in cubes:
                cube @ r

            await asyncio.sleep(ROTATION_FRAME_DURATION)

    def grab_update(self, mouse_event):
        # Horizontal movement rotates around vertical axis and vice-versa.
        alpha = np.pi * -self.mouse_dy / self.height  # vertical movement flipped, world coordinates opposite screen coordinates
        self.camera.rotate_x(alpha)

        beta = np.pi * self.mouse_dx / self.width
        self.camera.rotate_y(beta)

    def render(self, canvas_view, colors_view, rect):
        colors_buffer = self._colors_buffer

        frame_colors = self.background.current_frame.colors
        colors_buffer[::2] = frame_colors[..., :3]
        colors_buffer[1::2] = frame_colors[..., 3:]

        cam = self.camera
        cubes = list(self.cubes.flatten())
        cubes.sort(key=lambda cube: norm(cam.pos - cube.pos), reverse=True)

        for cube in cubes:
            cam.render_cube(cube, colors_buffer, self.aspect_ratio)

        np.concatenate((colors_buffer[::2], colors_buffer[1::2]), axis=-1, out=self.colors)

        super().render(canvas_view, colors_view, rect)
