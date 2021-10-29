import asyncio
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.tiled_image import TiledImage
from nurses_2.widgets.parallax import Parallax

IMAGES_DIR = Path("images")
SIZE = 30, 50

def load_parallax(path):
    sorted_dir = sorted(path.iterdir(), key=lambda path: path.stem)

    layers = [
        Image(size=SIZE, path=path)
        for path in sorted_dir if path.suffix == ".png"
    ]

    nlayers = len(layers)
    speeds = [1 / (nlayers - i) for i in range(nlayers)]

    return {"layers": layers, "speeds": speeds}


class MyApp(App):
    async def on_start(self):

        parallax_00 = Parallax(size=SIZE, **load_parallax(IMAGES_DIR / "parallax_00"))
        parallax_01 = Parallax(pos=(0, 50), size=SIZE, **load_parallax(IMAGES_DIR / "parallax_01"))

        self.root.add_widgets(parallax_00, parallax_01)

        async def circle_movement():
            angles = np.linspace(0, 2 * np.pi, 400)
            radius = 50

            while True:
                for theta in angles:
                    parallax_00.offset = radius * np.cos(theta), radius * np.sin(theta)
                    await asyncio.sleep(.016)

        async def horizontal_movement():
            while True:
                parallax_01.horizontal_offset += 1
                await asyncio.sleep(.08)

        asyncio.create_task(circle_movement())
        asyncio.create_task(horizontal_movement())


MyApp().run()
