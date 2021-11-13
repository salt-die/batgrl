from typing import NamedTuple

import numpy as np


class Particle:
    __slots__ = (
        "pos",
        "velocity",
        "acceleration",
        "density",
        "pressure",
    )

    def __init__(self, pos: tuple[int, int]=(0, 0)):
        self.pos = np.array(pos, dtype=float)
        self.velocity = np.zeros_like(self.pos)
        self.acceleration = np.zeros_like(self.pos)
        self.density = 0
        self.pressure = 0


class Rect(NamedTuple):
    top: int
    left: int
    bottom: int
    right: int

    def __contains__(self, particle: Particle):
        t, l, b, r, *_ = self
        y, x = particle.pos
        return t <= y < b and l <= x < r

    def __and__(self, other):
        return not (
            self.left > other.right
            or other.left > self.right
            or self.top > other.bottom
            or other.bottom > self.top
        )


class QuadTree:
    THRESHOLD = 4

    def __init__(self, extent: Rect):
        self.extent = extent
        self.particles = [ ]
        self.branches = [ ]

    def branch(self):
        if self.branches:
            return

        t, l, b, r = self.extent
        v_cut = b // 2
        h_cut = r // 2

        self.branches = [
            QuadTree(Rect(t, l, v_cut, h_cut)),
            QuadTree(Rect(t, h_cut, v_cut, r)),
            QuadTree(Rect(v_cut, l, b, h_cut)),
            QuadTree(Rect(v_cut, h_cut, b, r)),
        ]

    def insert(self, particle: Particle):
        ...

    def within_radius(self, center, radius):
        ...
