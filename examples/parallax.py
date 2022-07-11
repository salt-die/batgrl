import asyncio
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.parallax import Parallax

THIS_DIR = Path(__file__).parent
IMAGES_DIR = THIS_DIR / Path("images")
SIZE = 30, 50

def load_layers(path):
    sorted_dir = sorted(path.iterdir(), key=lambda path: path.stem)

    return [
        Image(size=SIZE, path=path)
        for path in sorted_dir if path.suffix == ".png"
    ]


class MyApp(App):
    async def on_start(self):

        parallax_00 = Parallax(size=SIZE, layers=load_layers(IMAGES_DIR / "parallax_00"))
        parallax_01 = Parallax(pos=(0, 50), size=SIZE, layers=load_layers(IMAGES_DIR / "parallax_01"))

        self.add_widgets(parallax_00, parallax_01)

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


MyApp(title="Parallax Example").run()
