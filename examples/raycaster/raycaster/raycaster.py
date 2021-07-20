from typing import List

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.image import Image
from nurses_2.colors import BLACK_ON_BLACK

from .camera import Camera, rotation_matrix

ROTATE_LEFT = rotation_matrix(-2 * np.pi / 30)
ROTATE_RIGHT = rotation_matrix(2 * np.pi / 30)


class RayCaster(Widget):
    max_hops = 20  # How far rays are cast.

    def __init__(
        self,
        *args,
        map: np.ndarray,  # len(map.shape) == 2, dtype=int
        camera: Camera,
        textures: List[np.ndarray],
        default_color=BLACK_ON_BLACK,
        default_char="▀",
        **kwargs,
        ):
        kwargs.pop('transparent', None)
        super().__init__(*args, **kwargs)

        self.map = map
        self.camera = camera
        self.dark_textures = textures
        self.bright_textures = [(texture * .5 + 127).astype(np.uint8) for texture in self.dark_textures]

        self.resize(self.dim)

    def resize(self, dim):
        super().resize(dim)

        width = self.width
        # Pre-calculate angle of rays cast.
        self._ray_angles = angles = np.ones((width, 2), dtype=np.float16)
        angles[:, 1] = np.linspace(-1, 1, width, endpoint=False)

        # Create buffers
        self._rotated_angles = np.zeros_like(angles)
        self._deltas = np.zeros_like(angles)
        self._steps = np.zeros_like(angles)
        self._sides = np.zeros_like(angles)
        self._pos_int = np.zeros((2,), dtype=np.int16)
        self._pos_frac = np.zeros((2,), dtype=np.float16)

    def cast_ray(self, column):
        """
        Cast a ray for a given column of the screen.
        """
        camera = self.camera
        camera_pos = camera.pos
        map = self.map

        ray_pos = self._pos_int
        ray_pos[:] = camera_pos

        ray_angle = self._rotated_angles[column]
        delta = self._deltas[column]
        step = self._steps[column]
        sides = self._sides[column]

        # Cast a ray until we hit a wall or hit max_hops
        for _ in range(self.max_hops):
            side = 0 if sides[0] < sides[1] else 1
            sides[side] += delta[side]
            ray_pos[side] += step[side]

            if texture_index := map[tuple(ray_pos)]:
                break
        else:  # No walls in range.
            return

        # Not euclidean distance to avoid fish-eye effect.
        distance = (
            ray_pos[side]
            - camera_pos[side]
            + (0 if step[side] == 1 else 1)
        ) / ray_angle[side]

        height = 2 * self.height
        line_height = int(height / distance) if distance else 1_000  # "infinity"
        if line_height == 0:
            return  # Draw nothing

        if line_height >= height:
            line_start = 0
            line_end = height - 1
        else:
            half_height = height // 2
            half_line = line_height // 2

            line_start = half_height - half_line
            line_end = half_height + half_line

        texture = (self.dark_textures if side else self.bright_textures)[texture_index - 1]
        tex_h, tex_w, _ = texture.shape

        wall_x = (camera_pos[1 - side] + distance * ray_angle[1 - side]) % 1

        tex_x = int(wall_x * tex_w)
        if (-1 if side == 1 else 1) * ray_angle[side] < 0:
            tex_x = tex_w - tex_x - 1

        drawn_height = line_end - line_start
        offset = (line_height - drawn_height) / 2
        ys = np.arange(drawn_height) + offset
        tex_ys = (ys * tex_h / line_height).astype(int)

        color_buffer = texture[tex_ys, tex_x].astype(np.float16)
        color_buffer *= np.e ** (-distance * .001)
        np.clip(color_buffer, 0, 255, out=color_buffer)

        start, start_offset = divmod(line_start, 2)
        if start_offset:
            upper, lower = slice(3, None), slice(3)
        else:
            upper, lower = slice(3), slice(3, None)

        end, end_offset = divmod(line_end, 2)

        colors = self.colors
        colors[start: end, column, upper] = color_buffer[:drawn_height - end_offset:2]
        colors[start: end, column, lower] = color_buffer[1::2]

    def render(self, canvas_view, colors_view, rect):
        self.colors[:, :] = self.default_color

        # Bring in to locals
        camera = self.camera
        pos_frac = self._pos_frac
        rotated_angles = self._rotated_angles
        deltas = self._deltas
        steps = self._steps
        sides = self._sides

        multiply = np.multiply
        divide = np.true_divide
        errstate = np.errstate

        width = self.width
        cast_ray = self.cast_ray

        # Early calculations on rays can be vectorized; fill buffers with these calculations.
        np.dot(self._ray_angles, camera.plane, out=rotated_angles)

        with errstate(divide="ignore"):
            divide(1.0, rotated_angles, out=deltas)
        np.absolute(deltas, out=deltas)

        np.sign(rotated_angles, out=steps)

        np.mod(camera.pos, 1.0, out=pos_frac)

        np.heaviside(steps, 1.0, out=sides)
        np.subtract(steps, pos_frac, out=sides)
        multiply(sides, steps, out=sides)
        multiply(sides, deltas, out=sides)

        for column in range(width):
            cast_ray(column)

        super().render(canvas_view, colors_view, rect)

    def on_press(self, key_press):
        camera = self.camera
        pos = camera.pos
        plane = camera.plane

        if key_press.key == 'w' or key_press.key == 's':
            direction = 1 if key_press.key == 'w' else -1
            y, x = pos + .1 * plane[0] * direction

            map = self.map

            if map[int(y), int(pos[1])] == 0:
                pos[0] = y

            if map[int(pos[0]), int(x)] == 0:
                pos[1] = x

        elif key_press.key == 'a':
            np.dot(plane, ROTATE_LEFT, out=plane)

        elif key_press.key == 'd':
            np.dot(plane, ROTATE_RIGHT, out=plane)
