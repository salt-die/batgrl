import asyncio

from .load_image import load_image


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
        self.textures = list(map(load_image, sources))
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
