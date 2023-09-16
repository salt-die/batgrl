"""
A sprite class for :class:`nurses_2.widgets.raycaster.Raycaster`.
"""
from dataclasses import dataclass, field

import numpy as np
from numpy.typing import NDArray


@dataclass(slots=True)
class Sprite:
    """
    A sprite for a raycaster.
    """

    pos: tuple[float, float]
    """Position of sprite on map."""

    texture_idx: int
    """Index of sprite texture."""

    _relative: NDArray[np.float64] = field(
        init=False, default_factory=lambda: np.zeros(2)
    )

    distance: np.float64 = field(init=False)
    """Distance from camera, set when :attr:`relative` is set."""

    @property
    def relative(self):
        """Vector from camera to sprite, set by the caster."""
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
