"""
This file is for testing purposes. It will be removed at some point.

"wasd" to move the camera.
"""
import asyncio
from pathlib import Path

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.auto_resize_behavior import AutoResizeBehavior

from .raycaster import RayCaster
from .rotation_matrix import rotation_matrix

FRAMES_DIR = Path("..") / "frames" / "spinner"
MAP = np.array(
    [
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
    ],
    dtype=np.uint8,
)
ROTATE_LEFT = rotation_matrix(-2 * np.pi / 30)
ROTATE_RIGHT = rotation_matrix(2 * np.pi / 30)


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


class AnimatedTexture:
    """
    An animated texture.

    Notes
    -----
    This is an example of how to use Texture protocol to provide
    animated textures to the raycaster.
    """
    def __init__(self, path, animation_speed=1/12):
        sources = sorted(path.iterdir(), key=lambda file: file.name)
        self.textures = [
            cv2.cvtColor(cv2.imread(str(source), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)
            for source in sources
        ]
        self.animation_speed = animation_speed
        self.current_frame = 0
        self._animation_task = asyncio.create_task(self.start_animation())

    @property
    def texture(self):
        return self.textures[self.current_frame]

    @property
    def shape(self):
        return self.texture.shape

    def __getitem__(self, key):
        return self.texture[key]

    async def start_animation(self):
        ntextures = len(self.textures)

        while True:
            await asyncio.sleep(self.animation_speed)
            self.current_frame += 1
            if self.current_frame >= ntextures:
                self.current_frame %= ntextures


class TestCaster(AutoResizeBehavior, RayCaster):
    def on_press(self, key_press):
        camera = self.camera
        pos = camera.pos
        plane = camera.plane

        if key_press.key == 'w' or key_press.key == 's':
            direction = 1 if key_press.key == 'w' else -1
            y, x = pos + .1 * plane[0] * direction

            map = self.map

            if map[int(y), int(pos[1])] == 0:
                pos[0] = y

            if map[int(pos[0]), int(x)] == 0:
                pos[1] = x

        elif key_press.key == 'a':
            np.dot(plane, ROTATE_LEFT, out=plane)

        elif key_press.key == 'd':
            np.dot(plane, ROTATE_RIGHT, out=plane)
        else:
            return False

        return True


class MyApp(App):
    async def on_start(self):
        raycaster = TestCaster(
            map=MAP,
            camera=MyCamera(),
            textures=[AnimatedTexture(path=FRAMES_DIR)],
        )

        self.root.add_widget(raycaster)


MyApp().run()
