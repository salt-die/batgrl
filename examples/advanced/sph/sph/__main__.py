import asyncio

import numpy as np
from batgrl.app import App
from batgrl.colors import AColor, Color
from batgrl.gadgets.graphics import Graphics, scale_geometry
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.text import Text

from .solver import SPHSolver

WATER_COLOR = AColor.from_hex("1e1ea8ff")
FILL_COLOR = Color.from_hex("2fa399")


class SPH(Graphics):
    def __init__(self, nparticles, **kwargs):
        super().__init__(**kwargs)
        self.sph_solver = SPHSolver(
            nparticles, scale_geometry(self._blitter, self.size)
        )

    def on_add(self):
        super().on_add()
        self._update_task = asyncio.create_task(self._update())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def on_key(self, key_event):
        if key_event.key == "r":
            self.sph_solver.init_dam()
            return True
        return False

    def on_mouse(self, mouse_event):
        if mouse_event.button == "no_button" or not self.collides_point(
            mouse_event.pos
        ):
            return False

        # Apply a force from click to every particle in the solver.
        my, mx = scale_geometry(self._blitter, self.to_local(mouse_event.pos))
        relative_positions = self.sph_solver.state[:, :2] - (my, mx)
        self.sph_solver.state[:, 2:4] += (
            1e2
            * relative_positions
            / np.linalg.norm(relative_positions, axis=-1, keepdims=True)
        )
        return True

    async def _update(self):
        while True:
            h, w = scale_geometry(self._blitter, self.size)
            solver = self.sph_solver
            solver.step()
            positions = solver.state[:, :2]

            ys, xs = positions.astype(int).T
            xs = xs + (w - solver.WIDTH) // 2  # Center the particles.

            # Some solver configurations are unstable. Clip positions to prevent errors.
            ys = np.clip(ys, 0, h - 1)
            xs = np.clip(xs, 0, w - 1)

            self.clear()
            self.texture[ys, xs] = WATER_COLOR

            await asyncio.sleep(0)


class SPHApp(App):
    async def on_start(self):
        height, width = 26, 51
        slider_settings = (
            ("H", "Smoothing Length", 0.4, 3.5),
            ("GAS_CONST", "Gas Constant", 500.0, 4000.0),
            ("REST_DENS", "Rest Density", 150.0, 500.0),
            ("VISC", "Viscosity", 0.0, 5000.0),
            ("MASS", "Mass", 10.0, 500.0),
            ("DT", "DT", 0.001, 0.03),
            ("GRAVITY", "Gravity", 0.0, 1e5),
            ("WIDTH", "Width", 5, width),
        )
        sliders_height = (len(slider_settings) + 1) // 2 * 2

        container = Text(size=(height, width), pos_hint={"y_hint": 0.5, "x_hint": 0.5})

        fluid = SPH(
            nparticles=300,
            pos=(sliders_height, 0),
            size=(height - sliders_height, width),
        )

        def create_callback(caption, attr, y, x):
            def update(value):
                setattr(fluid.sph_solver, attr, value)
                if isinstance(v := getattr(fluid.sph_solver, attr), int):
                    value = f"{v}"
                else:
                    value = f"{v:.4}"
                container.add_str(f"{caption}: {value}".ljust(width // 2), pos=(y, x))

            return update

        container.add_gadget(fluid)
        for i, (attr, caption, min, max) in enumerate(slider_settings):
            y = i // 2 * 2
            x = (i % 2) * (width // 2 + 1)
            slider = Slider(
                pos=(y + 1, x),
                min=min,
                max=max,
                start_value=getattr(fluid.sph_solver, attr),
                callback=create_callback(caption, attr, y, x),
                size=(1, width // 2),
                fill_color=FILL_COLOR,
                slider_color=WATER_COLOR[:3],
            )
            container.add_gadget(slider)
        self.add_gadget(container)


if __name__ == "__main__":
    SPHApp(title="Smoothed-Particle Hydrodynamics").run()
