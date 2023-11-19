"""
A particle field example.

Controls:
- 'ctrl+c' to quit
- 'r' to reset
- 'click' to poke
"""
import asyncio
from pathlib import Path

import numpy as np
from batgrl.app import App
from batgrl.colors import BLACK, DEFAULT_COLOR_THEME, ColorPair, gradient
from batgrl.figfont import FIGFont
from batgrl.gadgets.gadget import Char, Gadget
from batgrl.gadgets.text_field import TextParticleField
from batgrl.io import MouseButton

ASSETS = Path(__file__).parent.parent / "assets"
BIG_FONT = FIGFont.from_path(ASSETS / "delta_corps_priest_1.flf")
LOGO = BIG_FONT.render_array("batgrl")
HEIGHT, WIDTH = LOGO.shape
LOGO = np.append(LOGO, [list("badass terminal graphics library".center(WIDTH))], axis=0)
HEIGHT += 1

POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = 0.99

NCOLORS = 100
YELLOW_ON_BLACK = ColorPair.from_colors(
    DEFAULT_COLOR_THEME.button_press.bg_color, BLACK
)
BLUE_ON_BLACK = ColorPair.from_colors(DEFAULT_COLOR_THEME.primary.bg_color, BLACK)
YELLOW_TO_BLACK = gradient(YELLOW_ON_BLACK, BLUE_ON_BLACK, NCOLORS // 2)
GRADIENT = np.array(YELLOW_TO_BLACK + YELLOW_TO_BLACK[::-1])

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
        h = self.height // 2
        w = self.width // 2
        nh, nw = self._old_middle = h - HEIGHT // 2, w - WIDTH // 2

        real_positions = self.particle_properties["real_positions"]
        real_positions += nh - oh, nw - ow
        self.particle_properties["original_positions"] += nh - oh, nw - ow
        self.particle_positions[:] = real_positions.astype(int)

    def on_mouse(self, mouse_event):
        if mouse_event.button is MouseButton.LEFT and self.collides_point(
            mouse_event.position
        ):
            y, x = self.to_local(mouse_event.position)
            relative_distances = self.particle_positions - (y, x)

            distances_sq = (relative_distances**2).sum(axis=1)
            distances_sq[distances_sq == 0] = 1

            self.particle_properties["velocities"] += (
                POWER * relative_distances / distances_sq[:, None]
            )

            if self._update_task.done():
                self._reset_task.cancel()
                self._update_task = asyncio.create_task(self.update())

    def on_key(self, key_event):
        if key_event.key == "r" and self._reset_task.done():
            self._reset_task = asyncio.create_task(self.reset())

    async def update(self):
        """Coroutine that updates color and position due to velocity."""
        positions = self.particle_positions
        real_positions = self.particle_properties["real_positions"]
        velocities = self.particle_properties["velocities"]
        color_pairs = self.particle_color_pairs
        color_indices = self.particle_properties["indices"]

        while True:
            speeds = np.linalg.norm(velocities, axis=1)
            if (speeds < 0.001).all():
                return

            clipped_speeds = np.clip(speeds, None, MAX_PARTICLE_SPEED)

            color_indices = (
                color_indices + clipped_speeds * COLOR_CHANGE_SPEED
            ).astype(int) % NCOLORS
            color_pairs[:] = GRADIENT[color_indices]

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

            ys[top] *= -1
            xs[left] *= -1
            ys[bottom] = 2 * h - ys[bottom]
            xs[right] = 2 * w - xs[right]

            vys[top] *= -1
            vxs[left] *= -1
            vys[bottom] *= -1
            vxs[right] *= -1

            await asyncio.sleep(0)

    async def reset(self):
        """
        Coroutine that returns a particle to its starting position with original
        color.
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

            indices[:] = (percent_left * start_indices + percent * end_indices).astype(
                int
            )
            color_pairs[:] = GRADIENT[indices]

            await asyncio.sleep(0.03)


class ExplodingLogoApp(App):
    async def on_start(self):
        colors = np.full((HEIGHT, WIDTH), 0)

        particle_positions = np.argwhere(LOGO != " ")
        pys, pxs = particle_positions.T

        particles = LOGO[pys, pxs]
        particle_chars = np.zeros_like(particles, dtype=Char)
        particle_chars["char"] = particles

        particle_properties = dict(
            indices=colors[pys, pxs],
            original_positions=particle_positions.copy(),
            original_indices=colors[pys, pxs],
            real_positions=particle_positions.astype(float),
            velocities=np.zeros((len(particle_positions), 2), dtype=float),
        )

        particle_color_pairs = np.array(
            GRADIENT[particle_properties["indices"]], dtype=np.uint8
        )

        field = PokeParticleField(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            particle_positions=particle_positions,
            particle_chars=particle_chars,
            particle_color_pairs=particle_color_pairs,
            particle_properties=particle_properties,
            is_transparent=True,
        )

        # This background to show off field transparency.
        bg = Gadget(
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "top-left"},
            background_color_pair=BLUE_ON_BLACK.reversed(),
        )
        self.add_gadgets(bg, field)


if __name__ == "__main__":
    ExplodingLogoApp(title="batgrl").run()
