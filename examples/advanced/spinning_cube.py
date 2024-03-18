import asyncio
from pathlib import Path

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import Color
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.image import Image
from batgrl.geometry import lerp

ASSETS = Path(__file__).parent.parent / "assets"
BACKGROUND = ASSETS / "loudypixelsky.png"
POINTS = np.array(
    [
        [-1, -1, -1],
        [-1, -1, 1],
        [-1, 1, -1],
        [-1, 1, 1],
        [1, -1, -1],
        [1, -1, 1],
        [1, 1, -1],
        [1, 1, 1],
    ]
)
LINES = [
    [0, 1],
    [0, 2],
    [0, 4],
    [1, 3],
    [1, 5],
    [2, 3],
    [2, 6],
    [3, 7],
    [4, 5],
    [4, 6],
    [5, 7],
    [6, 7],
]
R, G, B = Color.from_hex("4ce05d")
RADIUS = 3**0.5  # The cube of points is inscribed in a circle with this radius
DIAMETER = 2 * RADIUS
MIN_BRIGHTNESS = 0.15
MAX_BRIGHTNESS = 1.0


def rotate_x(theta):
    cos = np.cos(theta)
    sin = np.sin(theta)

    return np.array(
        [
            [1, 0, 0],
            [0, cos, sin],
            [0, -sin, cos],
        ]
    )


def rotate_y(theta):
    cos = np.cos(theta)
    sin = np.sin(theta)

    return np.array(
        [
            [cos, 0, -sin],
            [0, 1, 0],
            [sin, 0, cos],
        ]
    )


def rotate_z(theta):
    cos = np.cos(theta)
    sin = np.sin(theta)

    return np.array(
        [
            [cos, sin, 0],
            [-sin, cos, 0],
            [0, 0, 1],
        ]
    )


def darken(depth):
    normalized_depth = (depth + RADIUS) / DIAMETER
    brightness = lerp(MIN_BRIGHTNESS, MAX_BRIGHTNESS, normalized_depth)
    return int(brightness * R), int(brightness * G), int(brightness * B), 255


class SpinningCube(Graphics):
    def on_add(self):
        super().on_add()
        self._spin_task = asyncio.create_task(self.spin_forever())

    def on_remove(self):
        self._spin_task.cancel()
        super().on_remove()

    async def spin_forever(self):
        x_angle = y_angle = z_angle = 0

        while True:
            self.clear()

            h, w = self.size
            scale = w // 4, h // 2
            offset = w // 2, h

            points = POINTS @ rotate_x(x_angle) @ rotate_y(y_angle) @ rotate_z(z_angle)
            points_2D = (points[:, 1::-1] * scale + offset).astype(int)
            depths = points[:, 2]

            lines = []
            for a, b in LINES:
                depth = (depths[a] + depths[b]) / 2

                lines.append(
                    (
                        points_2D[a],
                        points_2D[b],
                        darken(depth),
                        depth,
                    )
                )
            lines.sort(key=lambda p: p[3])

            for a, b, color, _ in lines:
                cv2.line(self.texture, a, b, color, 2)

            x_angle += 0.001333
            y_angle += 0.002
            z_angle += 0.002666

            await asyncio.sleep(0)


class SpinApp(App):
    async def on_start(self):
        self.add_gadgets(
            Image(path=BACKGROUND, size_hint={"height_hint": 1.0, "width_hint": 1.0}),
            SpinningCube(size_hint={"height_hint": 1.0, "width_hint": 1.0}),
        )


if __name__ == "__main__":
    SpinApp(title="Spinning Cube").run()
