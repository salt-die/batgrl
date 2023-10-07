from pathlib import Path

import numpy as np
from batgrl.app import App
from batgrl.gadgets.raycaster import Raycaster, Sprite
from batgrl.gadgets.texture_tools import read_texture

from .animated_texture import AnimatedTexture
from .camera import Camera

ASSETS = Path(__file__).parent.parent.parent.parent / "assets"
SPINNER = ASSETS / "spinner"
CEILING = ASSETS / "bluestone.png"
FLOOR = ASSETS / "greystone.png"
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


class RaycasterApp(App):
    async def on_start(self):
        sources = sorted(SPINNER.iterdir(), key=lambda file: file.name)
        textures = [read_texture(source) for source in sources]

        raycaster = Raycaster(
            map=MAP,
            camera=Camera(),
            wall_textures=[AnimatedTexture(textures)],
            light_wall_textures=[AnimatedTexture(textures, lighten=True)],
            sprites=[
                Sprite(pos=(2.5, 2.5), texture_idx=0),
                Sprite(pos=(2.5, 7.5), texture_idx=0),
                Sprite(pos=(7.5, 7.5), texture_idx=0),
                Sprite(pos=(7.5, 2.5), texture_idx=0),
            ],
            sprite_textures=[read_texture(SPRITE)],
            ceiling=read_texture(CEILING),
            floor=read_texture(FLOOR),
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )

        self.add_gadget(raycaster)


if __name__ == "__main__":
    RaycasterApp(title="Raycaster Example").run()
