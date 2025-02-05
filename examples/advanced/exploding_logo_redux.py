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
from batgrl.gadgets.graphic_field import Blitter, GraphicParticleField
from batgrl.gadgets.graphics import scale_geometry
from batgrl.gadgets.image import Image, Point, Size
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.toggle_button import ToggleButton
from batgrl.geometry.easings import out_bounce
from batgrl.texture_tools import read_texture, resize_texture

LOGO_SIZE = Size(18, 36)
POWER = 2
MAX_PARTICLE_SPEED = 10
FRICTION = 0.99
PERCENTS = [out_bounce(p) for p in np.linspace(0, 1, 30)]
ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_BACKGROUND = ASSETS / "background.png"
PATH_TO_LOGO_FULL = ASSETS / "python_discord_logo.png"


class PokeParticleField(GraphicParticleField):
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
        if self._reset_task is not None:
            self._reset_task.cancel()
        if self._update_task is not None:
            self._update_task.cancel()
        super().on_size()
        old_origin = self._origin
        h, w = self._size
        th, tw = LOGO_SIZE  # scale_geometry(self._blitter, LOGO_SIZE)
        self._origin = Point((h - th) // 2, (w - tw) // 2)
        dif = old_origin - self._origin
        self.particle_properties["original_positions"] -= dif
        self.particle_positions -= dif

    def on_mouse(self, mouse_event):
        if mouse_event.button == "left" and self.collides_point(mouse_event.pos):
            y, x = self.to_local(mouse_event.pos)

            relative_distances = self.particle_positions - (y, x)
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
        positions = self.particle_positions
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
        pos = self.particle_positions
        start = pos.copy()
        end = self.particle_properties["original_positions"]
        for percent in PERCENTS:
            pos[:] = (1 - percent) * start + percent * end
            await asyncio.sleep(0.03)
        pos[:] = end


class ExplodingLogoApp(App):
    async def on_start(self):
        background = Image(
            path=PATH_TO_BACKGROUND, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        field = PokeParticleField(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            alpha=0.7,
            blitter="sixel",
            is_transparent=False,
        )

        def toggle_cb(blitter):
            def cb(toggle):
                if toggle == "on":
                    field._origin = Point(0, 0)
                    field.blitter = blitter
                    texture = resize_texture(
                        read_texture(PATH_TO_LOGO_FULL),
                        scale_geometry(field.blitter, LOGO_SIZE),
                    )
                    field.particles_from_texture(texture)
                    field.particle_properties = {
                        "original_positions": field.particle_positions.copy(),
                        "velocities": np.zeros((field.nparticles, 2), float),
                    }
                    field.on_size()

            return cb

        buttons = [
            ToggleButton(
                label=blitter,
                callback=toggle_cb(blitter),
                pos=(i, 0),
                size=(1, 15),
                group=0,
            )
            for i, blitter in enumerate(Blitter.__args__)
        ]
        buttons[0].callback("on")

        def toggle_trans(toggle):
            field.is_transparent = toggle == "on"

        trans_button = ToggleButton(
            label="Transparent", callback=toggle_trans, size=(1, 15), pos=(4, 0)
        )

        def on_slide(p):
            field.alpha = p

        bg_color = ToggleButton.color_theme.button_normal.bg
        slider = Slider(
            min=0.0,
            max=1.0,
            start_value=0.7,
            callback=on_slide,
            size=(1, 15),
            pos=(5, 0),
            bg_color=bg_color,
        )

        self.add_gadgets(background, field, *buttons, trans_button, slider)


if __name__ == "__main__":
    ExplodingLogoApp(title="Exploding Logo Redux Example").run()
