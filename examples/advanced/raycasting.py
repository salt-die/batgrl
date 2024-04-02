"""A raycaster example that includes an animated texture."""

import asyncio
from itertools import cycle, pairwise
from pathlib import Path
from time import monotonic

import cv2
import numpy as np
from batgrl.app import App
from batgrl.gadgets.raycaster import Raycaster, RaycasterCamera, Sprite
from batgrl.gadgets.texture_tools import read_texture
from batgrl.gadgets.video import Video
from batgrl.geometry import lerp

ASSETS = Path(__file__).parent.parent / "assets"
SPINNER = ASSETS / "spinner.gif"
CHECKER = ASSETS / "checkered.png"
SPRITE = ASSETS / "pixel_python.png"
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


class VideoTexture(Video):
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
            map=MAP,
            camera=camera,
            wall_textures=[video],
            sprites=[Sprite(pos=points[i], texture_idx=0) for i in range(4)],
            sprite_textures=[read_texture(SPRITE)],
            floor=read_texture(CHECKER),
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )
        self.add_gadget(raycaster)

        last_time = monotonic()
        elapsed = 0

        TURN_DURATION = 0.75
        MOVE_DURATION = 1.5

        for i, j in pairwise(cycle(range(4))):
            u, v = angles[i], angles[j]
            if v > u:
                v -= 2 * np.pi

            while elapsed < TURN_DURATION:
                current_time = monotonic()
                elapsed += current_time - last_time
                last_time = current_time
                camera.theta = lerp(u, v, elapsed / TURN_DURATION)
                raycaster.cast_rays()
                await asyncio.sleep(0)

            camera.theta = v
            elapsed -= TURN_DURATION

            while elapsed < MOVE_DURATION:
                current_time = monotonic()
                elapsed += current_time - last_time
                last_time = current_time

                camera.pos = lerp(points[i], points[j], elapsed / MOVE_DURATION)
                raycaster.cast_rays()
                await asyncio.sleep(0)

            camera.pos = points[j]
            elapsed -= MOVE_DURATION


if __name__ == "__main__":
    RaycasterApp(title="Raycaster Example").run()
