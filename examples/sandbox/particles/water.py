from nurses_2.colors import Color

from .particle import LiquidParticle


class Water(LiquidParticle):
    COLOR = Color(20, 100, 170)

    def collides(self, other):
        ...
