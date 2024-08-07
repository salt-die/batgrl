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
from batgrl.colors import Color
from batgrl.figfont import FIGFont
from batgrl.gadgets.pane import Cell, Pane
from batgrl.gadgets.text_field import TextParticleField, particle_data_from_canvas


def make_logo():
    assets = Path(__file__).parent.parent / "assets"
    font = FIGFont.from_path(assets / "delta_corps_priest_1.flf")
    logo = font.render_array("batgrl")
    return np.append(
        logo, [list("badass terminal graphics library".center(logo.shape[1]))], axis=0
    )


LOGO = make_logo()
HEIGHT, WIDTH = LOGO.shape

POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = 0.99

NCOLORS = 100
YELLOW = Color.from_hex("c4a219")
BLUE = Color.from_hex("070c25")

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
        if mouse_event.button == "left" and self.collides_point(mouse_event.pos):
            y, x = self.to_local(mouse_event.pos)
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
        positions = self.particle_positions
        real_positions = self.particle_properties["real_positions"]
        velocities = self.particle_properties["velocities"]

        while True:
            speeds = np.linalg.norm(velocities, axis=1)
            if (speeds < 0.001).all():
                return

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
        self._update_task.cancel()
        self.particle_properties["velocities"][:] = 0

        pos = self.particle_positions
        start = pos.copy()
        end = self.particle_properties["original_positions"]
        real = self.particle_properties["real_positions"]

        for percent in PERCENTS:
            percent_left = 1 - percent

            real[:] = percent_left * start + percent * end
            pos[:] = real.astype(int)

            await asyncio.sleep(0.03)


class ExplodingLogoApp(App):
    async def on_start(self):
        cell_arr = np.zeros_like(LOGO, dtype=Cell)
        cell_arr["char"] = LOGO
        cell_arr["fg_color"] = YELLOW
        positions, cells = particle_data_from_canvas(cell_arr)

        props = dict(
            original_positions=positions.copy(),
            real_positions=positions.astype(float),
            velocities=np.zeros((len(positions), 2), dtype=float),
        )

        field = PokeParticleField(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            particle_positions=positions,
            particle_cells=cells,
            particle_properties=props,
            is_transparent=True,
        )

        # This background to show off field transparency.
        bg = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 1.0, "anchor": "right"},
            bg_color=BLUE,
        )
        self.add_gadgets(bg, field)


if __name__ == "__main__":
    ExplodingLogoApp(title="batgrl").run()
