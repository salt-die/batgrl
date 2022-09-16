"""
Credit for ascii art logo to Matthew Barber (https://ascii.matthewbarber.io/art/python/)

Directions:
    'ctrl+c' to quit
    'r' to reset
    'click' to poke
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import rainbow_gradient, ColorPair, BLACK
from nurses_2.io import MouseButton
from nurses_2.widgets.particle_field.text_field import TextParticleField

LOGO = """
                   _.gj8888888lkoz.,_
                d888888888888888888888b,
               j88P""V8888888888888888888
               888    8888888888888888888
               888baed8888888888888888888
               88888888888888888888888888
                            8888888888888
    ,ad8888888888888888888888888888888888  888888be,
   d8888888888888888888888888888888888888  888888888b,
  d88888888888888888888888888888888888888  8888888888b,
 j888888888888888888888888888888888888888  88888888888p,
j888888888888888888888888888888888888888'  8888888888888
8888888888888888888888888888888888888^"   ,8888888888888
88888888888888^'                        .d88888888888888
8888888888888"   .a8888888888888888888888888888888888888
8888888888888  ,888888888888888888888888888888888888888^
^888888888888  888888888888888888888888888888888888888^
 V88888888888  88888888888888888888888888888888888888Y
  V8888888888  8888888888888888888888888888888888888Y
   `"^8888888  8888888888888888888888888888888888^"'
               8888888888888
               88888888888888888888888888
               8888888888888888888P""V888
               8888888888888888888    888
               8888888888888888888baed88V
                `^888888888888888888888^
                  `'"^^V888888888V^^'
"""
HEIGHT, WIDTH = 28, 56

POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = .99

NCOLORS = 100
RAINBOW = np.array([
    list(ColorPair.from_colors(fg_color, BLACK))
    for fg_color in rainbow_gradient(NCOLORS)
])
BLUE_INDEX = round(.65 * NCOLORS)
YELLOW_INDEX = round(.1 * NCOLORS)

COLOR_CHANGE_SPEED = 5
PERCENTS = tuple(np.linspace(0, 1, 30))


class PokeParticleField(TextParticleField):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._old_middle = 0, 0

    def on_add(self):
        super().on_add()
        self._reset_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._update_task = asyncio.create_task(self.update())

    def on_remove(self):
        super().on_remove()
        self._reset_task.cancel()
        self._update_task.cancel()

    def on_size(self):
        super().on_size()
        oh, ow = self._old_middle
        h, w = self.center
        nh, nw = self._old_middle = h - HEIGHT // 2, w - WIDTH // 2

        real_positions = self.particle_properties["real_positions"]
        real_positions += nh - oh, nw - ow
        self.particle_properties["original_positions"] += nh - oh, nw - ow
        self.particle_positions[:] = real_positions.astype(int)

    def on_mouse(self, mouse_event):
        if (
            mouse_event.button is MouseButton.LEFT
            and self.collides_point(mouse_event.position)
         ):
            y, x = self.to_local(mouse_event.position)
            relative_distances = self.particle_positions - (y, x)

            distances_sq = (relative_distances ** 2).sum(axis=1)
            distances_sq[distances_sq == 0] = 1

            self.particle_properties["velocities"] += POWER * relative_distances / distances_sq[:, None]

            if self._update_task.done():
                self._reset_task.cancel()
                self._update_task = asyncio.create_task(self.update())

    def on_key(self, key_event):
        if key_event.key == "r" and self._reset_task.done():
            self._reset_task = asyncio.create_task(self.reset())

    async def update(self):
        """
        Coroutine that updates color and position due to velocity.
        """
        positions = self.particle_positions
        real_positions = self.particle_properties["real_positions"]
        velocities = self.particle_properties["velocities"]
        color_pairs = self.particle_color_pairs
        color_indices = self.particle_properties["indices"]

        while True:
            speeds = np.linalg.norm(velocities, axis=1)
            if (speeds < .001).all():
                return

            clipped_speeds = np.clip(speeds, None, MAX_PARTICLE_SPEED)

            color_indices = (color_indices + clipped_speeds * COLOR_CHANGE_SPEED).astype(int) % NCOLORS
            color_pairs[:] = RAINBOW[color_indices]

            speed_mask = speeds > MAX_PARTICLE_SPEED
            velocities[speed_mask] *= MAX_PARTICLE_SPEED / speeds[:, None][speed_mask]

            real_positions += velocities
            velocities *= FRICTION
            positions[:] = real_positions.astype(int)

            # Boundary conditions
            ys, xs = positions.T
            vys, vxs = velocities.T

            h, w = self.size

            top = ys < 0
            left = xs < 0
            bottom = ys >= h
            right = xs >= w

            ys[top]    *= -1
            xs[left]   *= -1
            ys[bottom] = 2 * h - ys[bottom]
            xs[right]  = 2 * w - xs[right]

            vys[top]    *= -1
            vxs[left]   *= -1
            vys[bottom] *= -1
            vxs[right]  *= -1

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    async def reset(self):
        """
        Coroutine that returns a particle to its starting position with original color.
        """
        self._update_task.cancel()
        self.particle_properties["velocities"][:] = 0

        pos = self.particle_positions
        start = pos.copy()
        end = self.particle_properties["original_positions"]
        real = self.particle_properties["real_positions"]

        indices = self.particle_properties["indices"]
        start_indices = indices.copy()
        end_indices = self.particle_properties["original_indices"]
        color_pairs = self.particle_color_pairs

        for percent in PERCENTS:
            percent_left = 1 - percent

            real[:] = percent_left * start + percent * end
            pos[:] = real.astype(int)

            indices[:] = (percent_left * start_indices + percent * end_indices).astype(int)
            color_pairs[:] = RAINBOW[indices]

            try:
                await asyncio.sleep(0.03)
            except asyncio.CancelledError:
                return


class MyApp(App):
    async def on_start(self):
        colors = np.full((HEIGHT, WIDTH), BLUE_INDEX)
        colors[-7:] = colors[-13: -7, -41:] = YELLOW_INDEX
        colors[-14, -17:] = colors[-20: -14, -15:] = YELLOW_INDEX

        chars = np.array([list(line + " " * (WIDTH - len(line))) for line in LOGO.splitlines()])

        particle_positions = np.argwhere(chars != " ")
        pys, pxs = particle_positions.T

        particle_chars = chars[pys, pxs]

        particle_properties = dict(
            indices=colors[pys, pxs],
            original_positions=particle_positions.copy(),
            original_indices=colors[pys, pxs],
            real_positions=particle_positions.astype(float),
            velocities=np.zeros((len(particle_positions), 2), dtype=float),
        )

        particle_color_pairs = np.array(RAINBOW[particle_properties["indices"]], dtype=np.uint8)

        field = PokeParticleField(
            size_hint=(1.0, 1.0),
            particle_positions=particle_positions,
            particle_chars=particle_chars,
            particle_color_pairs=particle_color_pairs,
            particle_properties=particle_properties,
        )

        self.add_widget(field)


MyApp(title="Exploding Logo Example").run()
