from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.behaviors import AutoSizeBehavior
from nurses_2.widgets.raycaster import RayCaster

from .animated_texture import AnimatedTexture
from .camera import Camera

FRAMES_DIR = Path("..") / "frames" / "spinner"
IMAGES_DIR = Path("..") / "images"
CEILING_PATH = IMAGES_DIR / "bluestone.png"
FLOOR_PATH = IMAGES_DIR / "greystone.png"
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

def load_image(path):
    """
    Load an image as numpy array from a pathlib.Path.
    """
    path_str = str(path)
    bgr_image = cv2.imread(path_str, cv2.IMREAD_COLOR)
    rgb_image = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2RGB)
    return rgb_image


class AutoSizeCaster(AutoSizeBehavior, RayCaster):
    pass


class MyApp(App):
    async def on_start(self):
        sources = sorted(FRAMES_DIR.iterdir(), key=lambda file: file.name)
        textures = list(map(load_image, sources))

        raycaster = AutoSizeCaster(
            map=MAP,
            camera=Camera(),
            wall_textures=[ AnimatedTexture(textures) ],
            light_wall_textures=[ AnimatedTexture(textures, lighten=True) ],
            ceiling=load_image(CEILING_PATH),
            floor=load_image(FLOOR_PATH),
        )

        self.root.add_widget(raycaster)


MyApp().run()
