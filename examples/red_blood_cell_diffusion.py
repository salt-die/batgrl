import asyncio

import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.particle_field.graphic_field import (
    GraphicParticleField,
    GraphicParticle,
)
from nurses_2.colors import ARED, AColor

DARK_RED = AColor.from_hex("701402")

def add_polar_vectors(r1, a1, r2, a2):
    a = a2 - a1
    u = r2 * np.cos(a)
    v = r2 * np.sin(a)

    r = np.sqrt((r1 + u) ** 2 + v ** 2)
    a = a1 + np.arctan2(v, r1 + u)

    return r, a


class Circle(GraphicWidget):
    """
    A circle drawn with cv2.
    """
    def __init__(self, radius=10, **kwargs):
        super().__init__(**kwargs)
        self.radius = radius

    def update_geometry(self):
        super().update_geometry()
        h, w = self.size
        cv2.circle(self.texture, (w // 2, h - h % 2), self.radius, DARK_RED, thickness=-1)


class RedBloodCellDiffusion(GraphicParticleField):
    """
    Brownian motion with a barrier.
    """
    def __init__(
        self,
        rng,
        nparticles=100,
        barrier_radius=10.0,
        pass_probability=.001,
        step_distance=.2,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self.rng = rng

        self._radii = np.sqrt(rng.uniform(size=nparticles)) * barrier_radius / 5
        self._angles = rng.uniform(size=nparticles) * 2.0 * np.pi

        self.barrier_radius = barrier_radius
        self.pass_probability = pass_probability
        self.step_distance = step_distance

        for _ in range(nparticles):
            self.add_widget(GraphicParticle(color=ARED))

    def run(self):
        asyncio.create_task(self.step_forever())

    async def step_forever(self):
        while True:
            self._step()

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def _step(self):
        n = len(self.children)

        rng = self.rng
        step_angles = rng.random(size=n) * 2 * np.pi
        is_passing = rng.random(size=n) < self.pass_probability

        br = self.barrier_radius
        radii = self._radii
        angles = self._angles

        new_r, angles[:] = add_polar_vectors(
            radii,
            angles,
            self.step_distance,
            step_angles,
        )

        radii[:] = np.where(
              # Hasn't passed barrier #                      # Has passed barrier #
            ((radii < br) & ((new_r < br) | is_passing)) | ((radii > br) & (new_r > br)),
            new_r, radii
        )

        tops = radii * np.sin(angles) / 2 + self.height // 2
        lefts = (radii * np.cos(angles) + self.width // 2).astype(int)

        for cell, top, left in zip(self.children, tops, lefts):
            cell.top = top
            cell.left = left


class RedBloodCellDiffusionApp(App):
    async def on_start(self):
        simulation = RedBloodCellDiffusion(rng=np.random.default_rng(), size_hint=(1.0, 1.0))
        self.add_widgets(Circle(size_hint=(1.0, 1.0)), simulation)
        simulation.run()


RedBloodCellDiffusionApp(title="Red Blood Cell Diffusion").run()
