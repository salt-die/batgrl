"""
This file is for testing purposes. It will be removed at some point.

"wasd" to move the camera.
"""
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior

from .animated_texture import AnimatedTexture
from .load_image import load_image
from .raycaster import RayCaster
from .test_camera import MyCamera

FRAMES_DIR = Path("..") / "frames" / "spinner"
IMAGES_DIR = Path("..") / "images"
FLOOR_PATH = IMAGES_DIR / "greystone.png"
CEILING_PATH = IMAGES_DIR / "bluestone.png"
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


class AutoResizeCaster(AutoResizeBehavior, RayCaster):
    pass


class MyApp(App):
    async def on_start(self):
        light_anim = AnimatedTexture(path=FRAMES_DIR)
        light_anim.textures = [(63 + .72 * texture).astype(np.uint8) for texture in light_anim.textures]

        raycaster = AutoResizeCaster(
            map=MAP,
            camera=MyCamera(),
            textures=[ AnimatedTexture(path=FRAMES_DIR) ],
            light_textures=[ light_anim ],
            ceiling=load_image(CEILING_PATH),
            floor=load_image(FLOOR_PATH),
        )

        self.root.add_widget(raycaster)


MyApp().run()
