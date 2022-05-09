import asyncio

import cv2
import numpy as np

from nurses_2.colors import AWHITE, AColor
from nurses_2.io import MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget, Size

from .mesh import Mesh


class Cloth(GraphicWidget):
    def __init__(self, mesh_size: Size, scale=5, mesh_color: AColor=AWHITE, **kwargs):
        super().__init__(**kwargs)

        self.mesh = Mesh(mesh_size, nanchors=5)
        self.scale = scale
        self.mesh_color = mesh_color

        self.on_size()

    def on_size(self):
        h, w = self._size

        self.texture = np.full((h * 2, w, 4), self.default_color, dtype=np.uint8)

        # Center the nodes horizontally in the widget with following offset:
        self.h_offset = (self.width - self.mesh.nodes[-1].position.imag * self.scale) / 2 * 1j

    def step(self):
        """
        Step the mesh and draw a line for each link.
        """
        texture = self.texture
        texture[:] = self.default_color

        color = self.mesh_color
        mesh = self.mesh
        scale = self.scale
        h_offset = self.h_offset

        mesh.step()

        for link in mesh.links:
            a_pos = scale * link.a.position + h_offset
            ay, ax = int(a_pos.real), int(a_pos.imag)

            b_pos = scale * link.b.position + h_offset
            by, bx = int(b_pos.real), int(b_pos.imag)

            cv2.line(texture, (ax, ay), (bx, by), color)

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

        mouse_pos = complex(*self.to_local(mouse_event.position))
        scale = self.scale
        h_offset = self.h_offset

        for node in self.mesh.nodes:
            force_direction = scale * node.position + h_offset - mouse_pos
            magnitude = abs(force_direction)
            if magnitude != 0:
                force_normal = force_direction / magnitude
                node.acceleration -= .01 * force_normal

        return True
