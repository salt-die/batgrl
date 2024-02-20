"""A raycaster example that includes an animated texture."""
import asyncio
from pathlib import Path

import cv2
import numpy as np
from batgrl.app import App
from batgrl.gadgets.raycaster import Camera, Raycaster, Sprite
from batgrl.gadgets.texture_tools import read_texture
from batgrl.gadgets.video import Video

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
    """A video player that implements the `Texture` protocol."""

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
        points = [(2.5, 2.5), (2.5, 7.5), (7.5, 7.5), (7.5, 2.5)]
        angles = [np.pi, np.pi / 2, 0, 3 * np.pi / 2]

        video = VideoTexture(source=SPINNER)
        video.play()
        camera = Camera(pos=points[0], theta=angles[0])
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

        while True:
            for i in range(4):
                u, v = angles[i], angles[(i + 1) % 4]
                if v > u:
                    v -= 2 * np.pi
                for camera.theta in np.linspace(u, v, 10):
                    await asyncio.sleep(0.01)
                for camera.pos in np.linspace(points[i], points[(i + 1) % 4], 20):
                    await asyncio.sleep(0.01)


if __name__ == "__main__":
    RaycasterApp(title="Raycaster Example").run()
