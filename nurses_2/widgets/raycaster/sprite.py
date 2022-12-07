"""
A sprite class for :class:`nurses_2.widgets.raycaster.Raycaster`.
"""
import numpy as np


class Sprite:
    """
    A sprite for a raycaster.
    """
    __slots__ = "pos", "texture_idx", "_relative", "distance"

    def __init__(self, pos: np.ndarray, texture_idx: int):
        self.pos = pos
        self.texture_idx = texture_idx
        self.relative = np.array([0.0, 0.0])

    @property
    def relative(self):
        return self._relative

    @relative.setter
    def relative(self, value):
        self._relative = value
        self.distance = value @ value

    def __lt__(self, other):
        """
        Sprites are ordered by their distance to camera.
        """
        return self.distance > other.distance
