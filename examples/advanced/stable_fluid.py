# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "scipy",
# ]
# ///
"""
Stable fluid simulation.

Click to add fluid.
"r" to reset.
"""

import asyncio
from itertools import cycle

import numpy as np
from batgrl.app import App
from batgrl.colors import ABLACK, NEPTUNE_PRIMARY_BG, rainbow_gradient
from batgrl.gadgets.graphics import Graphics, scale_geometry
from batgrl.terminal.events import MouseEvent
from scipy.ndimage import convolve, map_coordinates

DIF_KERNEL = np.array([-0.5, 0.0, 0.5])
GRAD_KERNEL = np.array([-1.0, 0.0, 1.0])
GAUSSIAN_KERNEL = np.array(
    [
        [0.0625, 0.125, 0.0625],
        [0.125, 0.25, 0.125],
        [0.0625, 0.125, 0.0625],
    ]
)
PRESSURE_KERNEL = np.array(
    [
        [0.0, 0.25, 0.0],
        [0.25, 0.0, 0.25],
        [0.0, 0.25, 0.0],
    ]
)
CURL = 5.0
POKE_RADIUS = 3.0
DISSIPATION = 0.99
PRESSURE = 0.1
PRESSURE_ITERATIONS = 10
RAINBOW_COLORS = cycle(rainbow_gradient(100, alpha=255))
EPSILON = np.finfo(float).eps


class StableFluid(Graphics):
    def __init__(self, default_color=ABLACK, **kwargs):
        super().__init__(default_color=default_color, **kwargs)

    def on_add(self):
        super().on_add()
        self.on_size()
        self._update_task = asyncio.create_task(self._update())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def on_size(self):
        h, w = scale_geometry(self._blitter, self._size)
        self.texture = np.full((h, w, 4), self.default_color, dtype=np.uint8)
        self.dye = np.zeros((4, h, w))
        self.indices = np.indices((h, w))
        self.velocity = np.zeros((2, h, w))

    def on_mouse(self, mouse_event: MouseEvent):
        """Add dye on click."""
        if mouse_event.button == "no_button" or not self.collides_point(
            mouse_event.pos
        ):
            return False

        y, x = scale_geometry(self._blitter, self.to_local(mouse_event.pos))
        ys, xs = self.indices
        ry = ys - y
        rx = xs - x
        d = ry**2 + rx**2 + EPSILON

        if mouse_event.button == "left":
            self.velocity[0] += ry / d
            self.velocity[1] += rx / d
        else:
            self.velocity[0] -= ry / d
            self.velocity[1] -= rx / d

        poke_force = np.e ** (-d / POKE_RADIUS)
        self.dye += np.moveaxis(poke_force[..., None] * next(RAINBOW_COLORS), -1, 0)

        return True

    def on_key(self, key_event):
        if key_event.key.lower() == "r":
            self.on_size()  # Reset
            return True

    async def _update(self):
        while True:
            vy, vx = velocity = self.velocity

            # Vorticity
            ###########
            div_y = convolve(vy, DIF_KERNEL[None])
            div_x = convolve(vx, DIF_KERNEL[:, None])

            curl = div_y - div_x

            vort_y = convolve(curl, DIF_KERNEL[None])
            vort_x = convolve(curl, DIF_KERNEL[:, None])

            vorticity = np.stack((vort_x, vort_y))

            # Negating `vort_y`` and using `vorticity=np.stack((vort_y, vort_x))`
            # creates a more swirly effect, but there are line artifacts.

            vorticity /= np.linalg.norm(vorticity, axis=0) + EPSILON
            vorticity *= curl * CURL

            velocity += vorticity

            # Pressure Solver
            #################
            div = 0.25 * (div_y + div_x)

            pressure = np.full_like(div_y, PRESSURE)
            for _ in range(PRESSURE_ITERATIONS):
                convolve(pressure, PRESSURE_KERNEL, output=pressure)
                pressure -= div

            # Project
            #########
            vy -= convolve(pressure, GRAD_KERNEL[None])
            vx -= convolve(pressure, GRAD_KERNEL[:, None])

            # Advect
            ########
            coords = self.indices - velocity

            map_coordinates(vy, coords, output=vy, prefilter=False)
            map_coordinates(vx, coords, output=vx, prefilter=False)

            # Remove checkboard divergence and diffuse velocity.
            convolve(vy, GAUSSIAN_KERNEL, output=vy)
            convolve(vx, GAUSSIAN_KERNEL, output=vx)

            r, g, b, a = dye = self.dye
            map_coordinates(r, coords, output=r)
            map_coordinates(g, coords, output=g)
            map_coordinates(b, coords, output=b)
            map_coordinates(a, coords, output=a)

            dye *= DISSIPATION
            np.clip(dye, 0, 255, out=dye)

            self.texture[:] = np.moveaxis(dye, 0, -1)

            await asyncio.sleep(0)


class StableFluidApp(App):
    async def on_start(self):
        self.add_gadget(
            StableFluid(
                size_hint={"height_hint": 1.0, "width_hint": 1.0},
                default_color=(0, 0, 0, 0),
            )
        )


if __name__ == "__main__":
    StableFluidApp(title="Stable Fluid Example", bg_color=NEPTUNE_PRIMARY_BG).run()
