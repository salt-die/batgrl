import asyncio
import numpy as np

from nurses_2.app import App
from nurses_2.widgets.particle_field import HalfBlockField, HalfBlockParticle
from nurses_2.widgets.behaviors import AutoSizeBehavior
from nurses_2.colors import RED

def add_polar_vectors(r1, a1, r2, a2):
    a = a2 - a1
    u = r2 * np.cos(a)
    v = r2 * np.sin(a)

    r = np.sqrt((r1 + u) ** 2 + v ** 2)
    a = a1 + np.arctan2(v, r1 + u)

    return r, a


class RedBloodCell(HalfBlockParticle):
    @property
    def polar(self):
        return self._polar

    @polar.setter
    def polar(self, pos):
        self._polar = pos
        r, a = pos
        self.top = r * np.sin(a) + self.parent.height // 2
        self.left = int(r * np.cos(a)) + self.parent.width // 2


class RedBloodCellDiffusion(AutoSizeBehavior, HalfBlockField):
    def __init__(self,
        *args,
        rng,
        nparticles=50,
        radius=2.0,
        barrier_radius=10.0,
        pass_probability=.001,
        step_distance=.5,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.rng = rng

        self._coords = coords = np.zeros((nparticles, 2), dtype=float, order="F")
        coords[:, 0] += np.sqrt(rng.uniform(size=nparticles)) * radius
        coords[:, 1] += rng.uniform(size=nparticles) * 2.0 * np.pi

        self.barrier_radius = barrier_radius
        self.pass_probability = pass_probability
        self.step_distance = step_distance

        for _ in range(nparticles):
            self.add_widget(RedBloodCell(color=RED))

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
        coords = self._coords

        new_r, coords[:, 1] = add_polar_vectors(
            coords[:, 0],
            coords[:, 1],
            self.step_distance,
            step_angles,
        )

        coords[:, 0] = np.where(
              # Hasn't passed barrier #                             # Has passed barrier #
            ((coords[:, 0] < br) & ((new_r < br) | is_passing)) | ((coords[:, 0] > br) & (new_r > br)),
            new_r, coords[:, 0]
        )

        for particle, polar in zip(self.children, coords):
            particle.polar = polar


class RedBloodCellDiffusionApp(App):
    async def on_start(self):
        simulation = RedBloodCellDiffusion(rng=np.random.default_rng())
        self.root.add_widget(simulation)
        simulation.run()


RedBloodCellDiffusionApp(title="Red Blood Cell Diffusion").run()
