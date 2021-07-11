from nurses_2.colors import Color

from .particle import Particle


class Stone(Particle):
    COLOR = Color(120, 110, 120)

    def __init__(self, world, position):
        self.world = world
        self._pos = position

    @property
    def pos(self):
        return self._pos

    async def update(self):
        """
        Do nothing.
        """
