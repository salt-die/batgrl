import asyncio

import numpy as np


class AnimatedTexture:
    """
    An animated texture.
    """
    def __init__(self, textures, animation_speed=1/12, lighten=False):
        if lighten:
            self.textures = [(63 + .75 * texture).astype(np.uint8) for texture in textures]
        else:
            self.textures = textures

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
