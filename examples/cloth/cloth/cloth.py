import asyncio

import cv2
import numpy as np

from nurses_2.colors import BLUE, RED, gradient
from nurses_2.data_structures import Size
from nurses_2.io import MouseButton
from nurses_2.widgets import Widget

from .mesh import Mesh


class Cloth(Widget):
    def __init__(self, *args, mesh_size: Size, scale=5, default_char="▀", **kwargs):
        super().__init__(*args, default_char=default_char, **kwargs)

        pos_gradient = gradient(self.default_color_pair, RED, 10)
        self.neg_gradient = gradient(self.default_color_pair, BLUE, 10)

        self.mesh = Mesh(mesh_size, nanchors=5)
        self.scale = scale

        self.resize(self.size)  # Creates empty texture where links are drawn.

    def resize(self, size):
        super().resize(size)
        self.texture = np.full(
            (2 * size[0], size[1], 3),
            self.default_color_pair[3:],
            dtype=np.uint8,
        )

        # Center the nodes horizontally in the widget with following offset:
        self.h_offset = (self.width - self.mesh.nodes[-1].position.imag * self.scale) / 2 * 1j

    def step(self):
        """
        Step the mesh and draw a line for each link.
        """
        texture = self.texture
        texture[:] = self.default_color_pair[3:]

        mesh = self.mesh
        color = self.default_color_pair[:3]
        scale = self.scale
        h_offset = self.h_offset

        mesh.step()

        for link in mesh.links:
            a_pos = scale * link.a.position + h_offset
            ay, ax = int(a_pos.real), int(a_pos.imag)

            b_pos = scale * link.b.position + h_offset
            by, bx = int(b_pos.real), int(b_pos.imag)

            if link.stretch < 0:


            cv2.line(texture, (ax, ay), (bx, by), color)

        self.colors[..., :3] = texture[::2]
        self.colors[..., 3:] = texture[1::2]

    async def step_forever(self):
        while True:
            self.step()

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def on_click(self, mouse_event):
        if mouse_event.button != MouseButton.LEFT:
            return False

        mouse_pos = complex(*self.absolute_to_relative_coords(mouse_event.position))
        scale = self.scale
        h_offset = self.h_offset

        for node in self.mesh.nodes:
            force_direction = scale * node.position + h_offset - mouse_pos
            magnitude = abs(force_direction)
            if magnitude != 0:
                force_normal = force_direction / magnitude
                node.acceleration -= .01 * force_normal

        return True
