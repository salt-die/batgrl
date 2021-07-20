import asyncio
from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App

from .raycaster import RayCaster

LOGO = Path('..') / 'images' / 'python_discord_logo.png'
WALL_TEXTURE = cv2.cvtColor(cv2.imread(str(LOGO), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
MAP = np.array([
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
])


class MyCamera:
    FIELD_OF_VIEW = .6

    pos = np.array([4.5, 4.5], dtype=np.float16)
    plane = np.array(
        [
            [1, 0],
            [0, FIELD_OF_VIEW],
        ],
        dtype=np.float16,
    )


class MyApp(App):
    async def on_start(self):
        raycaster = RayCaster(
            dim=(31, 100),
            map=MAP,
            camera=MyCamera(),
            textures=[WALL_TEXTURE],
        )

        self.root.add_widget(raycaster)


MyApp().run()
