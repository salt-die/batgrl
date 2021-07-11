from nurses_2.colors import Color

from .particle import SolidParticle


class Sand(SolidParticle):
    COLOR = Color(150, 100, 50)

    def collides(self, other):
        ...
