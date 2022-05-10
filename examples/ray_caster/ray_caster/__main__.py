from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.ray_caster import RayCaster, Sprite

from .animated_texture import AnimatedTexture
from .camera import Camera

FRAMES_DIR = Path("..") / "frames" / "spinner"
IMAGES_DIR = Path("..") / "images"
CEILING_PATH = IMAGES_DIR / "bluestone.png"
FLOOR_PATH = IMAGES_DIR / "greystone.png"
SPRITE = IMAGES_DIR / "pixel_python.png"
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
    path = str(path)
    image = cv2.imread(path, cv2.IMREAD_UNCHANGED)

    if image.dtype == np.dtype(np.uint16):
        image = (image // 257).astype(np.uint8)
    elif image.dtype == np.dtype(np.float32):
        image = (image * 255).astype(np.uint8)

    # Add an alpha channel if there isn't one.
    h, w, c = image.shape
    if c == 3:
        default_alpha_channel = np.full((h, w, 1), 255, dtype=np.uint8)
        image = np.dstack((image, default_alpha_channel))

    return cv2.cvtColor(image, cv2.COLOR_BGRA2RGBA)


class MyApp(App):
    async def on_start(self):
        sources = sorted(FRAMES_DIR.iterdir(), key=lambda file: file.name)
        textures = list(map(load_image, sources))

        raycaster = RayCaster(
            map=MAP,
            camera=Camera(),
            wall_textures=[ AnimatedTexture(textures) ],
            light_wall_textures=[ AnimatedTexture(textures, lighten=True) ],
            sprites=[
                Sprite(pos=(2.5, 2.5), texture_idx=0),
                Sprite(pos=(2.5, 7.5), texture_idx=0),
                Sprite(pos=(7.5, 7.5), texture_idx=0),
                Sprite(pos=(7.5, 2.5), texture_idx=0),
            ],
            sprite_textures=[ load_image(SPRITE) ],
            ceiling=load_image(CEILING_PATH),
            floor=load_image(FLOOR_PATH),
            size_hint=(1.0, 1.0),
        )

        self.add_widget(raycaster)


MyApp(title="Raycaster Example").run()
