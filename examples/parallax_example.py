import asyncio
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.tiled_image import TiledImage
from nurses_2.widgets.parallax import Parallax

IMAGES_DIR = Path("images") / "parallax"
SIZE = 30, 100


class MyApp(App):
    async def on_start(self):
        sorted_dir =  sorted(IMAGES_DIR.iterdir(), key=lambda path: path.stem)
        layers = [
            Image(size=SIZE, path=path)
            for path in sorted_dir if path.suffix == ".png"
        ]

        nlayers = len(layers)
        speeds = [1 / (nlayers - i) for i in range(nlayers)]

        parallax = Parallax(size=SIZE, layers=layers, speeds=speeds)
        self.root.add_widget(parallax)

        angles = np.linspace(0, 2 * np.pi, 400)
        radius = 50

        while True:
            for theta in angles:
                parallax.offset = radius * np.cos(theta), radius * np.sin(theta)

                await asyncio.sleep(.016)


MyApp().run()
