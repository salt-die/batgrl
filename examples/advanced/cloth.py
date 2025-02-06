import asyncio
from dataclasses import dataclass

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import AWHITE, AColor
from batgrl.gadgets.graphics import Graphics, Size, scale_geometry
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.text import Text
from numpy.typing import NDArray

MESH_SIZE = 11, 21
DAMPING = 0.97
GRAVITY = np.array([0.015, 0])


@dataclass
class Node:
    position: NDArray[np.float64]

    def __post_init__(self):
        self.velocity = np.zeros(2)
        self.acceleration = np.zeros(2)
        self.is_anchored = False

    def step(self):
        if not self.is_anchored:
            self.velocity += self.acceleration
            self.position += self.velocity
            self.velocity *= DAMPING
        self.acceleration[:] = GRAVITY


@dataclass
class Link:
    a: Node
    b: Node

    def __post_init__(self):
        self.rest_length = np.linalg.norm(self.a.position - self.b.position)

    def step(self):
        direction = self.b.position - self.a.position
        length = np.linalg.norm(direction)
        stretch = (length - self.rest_length) / length
        if stretch > 0:
            momentum = direction * stretch * 0.5
            self.a.acceleration += momentum
            self.b.acceleration -= momentum


def make_mesh(size: Size) -> tuple[list[Node], list[Link]]:
    height, width = size

    nodes = [
        Node(position=np.array([y, x], dtype=float))
        for y in range(height)
        for x in range(width)
    ]

    links = []
    for y in range(height):
        for x in range(width):
            a = nodes[y * width + x]

            if y != height - 1:  # attach down
                b = nodes[(y + 1) * width + x]
                links.append(Link(a, b))

            if x != width - 1:  # attach right
                b = nodes[y * width + x + 1]
                links.append(Link(a, b))

    return nodes, links


class Cloth(Graphics):
    def __init__(self, mesh_size: Size, scale=5, mesh_color: AColor = AWHITE, **kwargs):
        self.nodes, self.links = make_mesh(mesh_size)
        self.scale = scale
        self.mesh_color = mesh_color
        super().__init__(**kwargs)
        self.on_size()

    def on_size(self):
        super().on_size()
        self.h_offset = (self.width - self.nodes[-1].position[1] * self.scale) / 2

    def scale_pos(self, pos: NDArray[np.float64]) -> NDArray[np.float64]:
        scaled = self.scale * pos
        scaled[1] += self.h_offset
        return scaled

    def step(self):
        self.clear()
        for link in self.links:
            link.step()
        for node in self.nodes:
            node.step()
        for link in self.links:
            cv2.line(
                self.texture,
                self.scale_pos(link.a.position).astype(int)[::-1],
                self.scale_pos(link.b.position).astype(int)[::-1],
                self.mesh_color,
            )

    def on_mouse(self, mouse_event):
        if mouse_event.button != "left":
            return False
        mouse_pos = np.array(
            scale_geometry(self._blitter, self.to_local(mouse_event.pos))
        )
        for node in self.nodes:
            force_direction = self.scale_pos(node.position) - mouse_pos
            magnitude = np.linalg.norm(force_direction)
            if magnitude != 0:
                force_normal = force_direction / magnitude
                node.acceleration -= 0.01 * force_normal
        return True


class ClothApp(App):
    async def on_start(self):
        cloth = Cloth(
            mesh_size=MESH_SIZE, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        slider_label = Text(size=(1, 11))

        def update_anchors(nanchors):
            nanchors = round(nanchors)
            slider_label.add_str(f"Anchors: {nanchors:02d}")
            height, width = MESH_SIZE
            for y in range(height):
                for x in range(width):
                    node = cloth.nodes[y * width + x]
                    node.position[:] = y, x
                    node.is_anchored = False
            for i in np.linspace(0, width - 1, nanchors).astype(int):
                cloth.nodes[i].is_anchored = True

        slider = Slider(
            size=(1, 11), min=2, max=13, start_value=5, callback=update_anchors
        )
        slider.top = slider_label.bottom
        self.add_gadgets(cloth, slider_label, slider)
        while True:
            cloth.step()
            await asyncio.sleep(0)


if __name__ == "__main__":
    ClothApp(title="Cloth Simulation").run()
