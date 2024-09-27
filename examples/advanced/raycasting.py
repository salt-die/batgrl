"""Showcase of batgrl's raycasters."""

import asyncio
from itertools import cycle, pairwise
from pathlib import Path
from time import perf_counter

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import GREEN
from batgrl.gadgets.raycaster import Raycaster, RaycasterCamera, RgbaTexture, Sprite
from batgrl.gadgets.text_raycaster import TextRaycaster
from batgrl.gadgets.video import Video
from batgrl.geometry import lerp
from batgrl.text_tools import new_cell
from batgrl.texture_tools import read_texture


def load_assets():
    assets = Path(__file__).parent.parent / "assets"

    yield assets / "spinner.gif"

    checker = assets / "checkered.png"
    yield read_texture(checker)

    python_sprite = assets / "pixel_python.png"
    yield read_texture(python_sprite)

    wall = assets / "wall.txt"
    yield np.array(
        [[int(char) for char in line] for line in wall.read_text().splitlines()]
    )

    tree = assets / "tree.txt"
    yield np.array([list(line) for line in tree.read_text().splitlines()])


SPINNER, CHECKER, PYTHON, WALL, TREE = load_assets()
MAP = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    dtype=np.uint8,
)


class VideoTexture(Video, RgbaTexture):
    """A video player that implements the `RgbaTexture` protocol."""

    def __init__(self, source):
        super().__init__(source=source)
        oh = self._resource.get(cv2.CAP_PROP_FRAME_HEIGHT)
        ow = self._resource.get(cv2.CAP_PROP_FRAME_WIDTH)
        self.size = oh // 2, ow

    @property
    def shape(self):
        """Shape of the texture."""
        return self.texture.shape

    def __getitem__(self, key):
        return self.texture[key]


class RaycasterApp(App):
    """A raycaster app."""

    async def on_start(self):
        points = np.array([[2.5, 2.5], [2.5, 7.5], [7.5, 7.5], [7.5, 2.5]])
        angles = [np.pi, np.pi / 2, 0, 3 * np.pi / 2]

        video = VideoTexture(source=SPINNER)
        video.play()
        camera = RaycasterCamera(pos=points[0], theta=angles[0])
        raycaster = Raycaster(
            caster_map=MAP,
            camera=camera,
            wall_textures=[video],
            sprites=[Sprite(pos=points[i], texture_idx=0) for i in range(4)],
            sprite_textures=[PYTHON],
            floor=CHECKER,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
        )
        text_raycaster = TextRaycaster(
            caster_map=MAP,
            camera=camera,
            wall_textures=[WALL],
            sprites=[Sprite(pos=points[i], texture_idx=0) for i in range(4)],
            sprite_textures=[TREE],
            default_cell=new_cell(fg_color=GREEN),
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "left"},
        )
        self.add_gadgets(raycaster, text_raycaster)

        turn_duration = 0.75
        move_duration = 1.5
        last_time = perf_counter()
        elapsed = 0

        for i, j in pairwise(cycle(range(4))):
            u, v = angles[i], angles[j]
            if v > u:
                v -= 2 * np.pi

            while elapsed < turn_duration:
                current_time = perf_counter()
                elapsed += current_time - last_time
                last_time = current_time
                camera.theta = lerp(u, v, elapsed / turn_duration)
                raycaster.cast_rays()
                text_raycaster.cast_rays()
                await asyncio.sleep(0)

            camera.theta = v
            elapsed -= turn_duration

            while elapsed < move_duration:
                current_time = perf_counter()
                elapsed += current_time - last_time
                last_time = current_time

                camera.pos = lerp(points[i], points[j], elapsed / move_duration)
                raycaster.cast_rays()
                text_raycaster.cast_rays()
                await asyncio.sleep(0)

            camera.pos = points[j]
            elapsed -= move_duration


if __name__ == "__main__":
    RaycasterApp(title="Raycasting Example").run()
