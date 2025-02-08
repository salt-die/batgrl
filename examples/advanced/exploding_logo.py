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
from batgrl.gadgets.pane import Cell, Pane, Point, Size
from batgrl.gadgets.text_field import TextParticleField
from batgrl.geometry.easings import in_exp


def make_logo():
    assets = Path(__file__).parent.parent / "assets"
    font = FIGFont.from_path(assets / "delta_corps_priest_1.flf")
    logo = font.render_array("batgrl")
    return np.append(
        logo, [list("badass terminal graphics library".center(logo.shape[1]))], axis=0
    )


LOGO = make_logo()
LOGO_SIZE = Size(*LOGO.shape)

POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = 0.99

NCOLORS = 100
YELLOW = Color.from_hex("c4a219")
BLUE = Color.from_hex("123456")

COLOR_CHANGE_SPEED = 5
PERCENTS = [in_exp(p) for p in np.linspace(0, 1, 30)]


class PokeParticleField(TextParticleField):
    _origin = Point(0, 0)
    _reset_task: asyncio.Task | None = None
    _update_task: asyncio.Task | None = None

    def on_remove(self):
        super().on_remove()
        if self._reset_task is not None:
            self._reset_task.cancel()
        if self._update_task is not None:
            self._update_task.cancel()

    def on_size(self):
        super().on_size()
        if self._reset_task is not None:
            self._reset_task.cancel()
        if self._update_task is not None:
            self._update_task.cancel()
        old_origin = self._origin
        self._origin = self.center - LOGO_SIZE.center
        dif = old_origin - self._origin
        self.particle_properties["original_positions"] -= dif
        self.particle_coords -= dif

    def on_mouse(self, mouse_event):
        if mouse_event.button == "left" and self.collides_point(mouse_event.pos):
            y, x = self.to_local(mouse_event.pos)
            relative_distances = self.particle_coords - (y, x)

            distances_sq = (relative_distances**2).sum(axis=1)
            distances_sq[distances_sq == 0] = 1

            self.particle_properties["velocities"] += (
                POWER * relative_distances / distances_sq[:, None]
            )

            if self._reset_task is not None:
                self._reset_task.cancel()
            if self._update_task is None or self._update_task.done():
                self._update_task = asyncio.create_task(self.update())

    def on_key(self, key_event):
        if key_event.key == "r" and (
            self._reset_task is None or self._reset_task.done()
        ):
            self._reset_task = asyncio.create_task(self.reset())

    async def update(self):
        positions = self.particle_coords
        velocities = self.particle_properties["velocities"]

        while True:
            speeds = np.linalg.norm(velocities, axis=1)
            if (speeds < 0.001).all():
                return

            speed_mask = speeds > MAX_PARTICLE_SPEED
            velocities[speed_mask] *= MAX_PARTICLE_SPEED / speeds[:, None][speed_mask]

            positions += velocities
            velocities *= FRICTION

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
        if self._update_task is not None:
            self._update_task.cancel()
        self.particle_properties["velocities"][:] = 0
        pos = self.particle_coords
        start = pos.copy()
        end = self.particle_properties["original_positions"]
        for percent in PERCENTS:
            pos[:] = (1 - percent) * start + percent * end
            await asyncio.sleep(0.03)
        pos[:] = end


class ExplodingLogoApp(App):
    async def on_start(self):
        cell_arr = np.zeros_like(LOGO, dtype=Cell)
        cell_arr["char"] = LOGO
        cell_arr["fg_color"] = YELLOW

        field = PokeParticleField(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}, is_transparent=True
        )
        field.particles_from_cells(cell_arr)
        field.particle_properties = {
            "original_positions": field.particle_coords.copy(),
            "velocities": np.zeros((field.nparticles, 2), dtype=float),
        }

        # This background to show off field transparency.
        bg = Pane(
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 1.0, "anchor": "right"},
            bg_color=BLUE,
        )
        self.add_gadgets(bg, field)


if __name__ == "__main__":
    ExplodingLogoApp(title="batgrl").run()
