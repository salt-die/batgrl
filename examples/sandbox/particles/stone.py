from nurses_2.colors import Color

from .base import Solid


class Stone(Solid):
    COLOR = Color(120, 110, 120)

    def __init__(self, world, position):
        self.world = world
        self._pos = position
