"""
Click to add fluid. `r` to reset.

`cv2` convolutions (`filter2D`) currently don't support boundary wrapping. This is done
manually by creating pressure and momentum arrays with sizes equal to the gadget's
texture's size plus a 2-width border and copying data into that border.
"""

import asyncio
from typing import Literal

import numpy as np
from batgrl.app import App
from batgrl.colors import Color
from batgrl.gadgets.graphics import Graphics, scale_geometry
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.text import Text
from batgrl.gadgets.toggle_button import ToggleButton
from cv2 import filter2D

# Kernels
CONVECTION = np.array(
    [
        [0, 0.25, 0],
        [0.25, -1, 0.25],
        [0, 0.25, 0],
    ]
)
DIFFUSION = np.array(
    [
        [0.025, 0.1, 0.025],
        [0.1, 0.5, 0.1],
        [0.025, 0.1, 0.025],
    ]
)
POISSON = np.array(
    [
        [0, 0.25, 0],
        [0.25, 0, 0.25],
        [0, 0.25, 0],
    ]
)
WATER_COLOR = Color.from_hex("1259FF")
BINARY = np.array([Color.from_hex("0606fa"), Color.from_hex("0f080e")])


def wrap_border(array):
    array[:2] = array[-4:-2][::-1]
    array[-2:] = array[2:4][::-1]
    array[2:-2, :2] = array[2:-2, -4:-2][::-1]
    array[2:-2, -2:] = array[2:-2, 2:4][::-1]


def sigmoid(array):
    return 1 / (1 + np.e**-array)


class Fluid(Graphics):
    mode: Literal["smooth", "binary"] = "smooth"
    visual: Literal["momentum", "pressure"] = "pressure"
    damping: float = 0.99

    def on_add(self):
        super().on_add()
        self.on_size()
        self._update_task = asyncio.create_task(self._update())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def on_size(self):
        h, w = scale_geometry(self._blitter, self._size)
        size_with_border = h + 4, w + 4

        self.texture = np.zeros((h, w, 4), dtype=np.uint8)
        self.pressure = np.zeros(size_with_border, dtype=float)
        self.momentum = np.zeros(size_with_border, dtype=float)

    def on_mouse(self, mouse_event):
        if not self.collides_point(mouse_event.pos):
            return False

        if mouse_event.button != "no_button":
            y, x = scale_geometry(self._blitter, self.to_local(mouse_event.pos))
            self.pressure[y + 2 : y + 4, x + 2 : x + 4] += 2.0
            return True

    def on_key(self, key_event):
        if key_event.key.lower() == "r":
            self.on_size()  # Reset
            return True

    async def _update(self):
        while True:
            pressure = self.pressure
            momentum = self.momentum

            wrap_border(momentum)
            wrap_border(pressure)

            self.momentum = filter2D(momentum, -1, DIFFUSION) + filter2D(
                pressure, -1, CONVECTION
            )

            delta = filter2D(self.momentum, -1, POISSON)

            self.pressure = filter2D(pressure, -1, POISSON) + 0.5 * (delta - delta**2)
            self.pressure *= self.damping

            if self.visual == "momentum":
                arr = self.momentum
            else:
                arr = self.pressure

            if self.mode == "binary":
                indices = (sigmoid(arr[2:-2, 2:-2]) * 2).astype(int)
                self.texture[..., :3] = BINARY[indices]
            else:
                self.texture[..., :3] = (
                    sigmoid(arr[2:-2, 2:-2, None]) * WATER_COLOR
                ).astype(np.uint8)
            self.texture[..., 3] = 255
            await asyncio.sleep(0)


class NavierStokesApp(App):
    async def on_start(self):
        fluid = Fluid(size_hint={"height_hint": 1.0, "width_hint": 1.0})

        def on_smooth(toggle_state):
            if toggle_state == "on":
                fluid.mode = "smooth"

        def on_binary(toggle_state):
            if toggle_state == "on":
                fluid.mode = "binary"

        smooth_toggle = ToggleButton(
            label="smooth", group=0, callback=on_smooth, size=(1, 9)
        )
        binary_toggle = ToggleButton(
            label="binary", group=0, callback=on_binary, pos=(1, 0), size=(1, 9)
        )

        def on_momentum(toggle_state):
            if toggle_state == "on":
                fluid.visual = "momentum"

        def on_pressure(toggle_state):
            if toggle_state == "on":
                fluid.visual = "pressure"

        momentum_toggle = ToggleButton(
            label="momentum", group=1, callback=on_momentum, size=(1, 11), pos=(0, 10)
        )
        pressure_toggle = ToggleButton(
            label="pressure", group=1, callback=on_pressure, size=(1, 11), pos=(1, 10)
        )

        damp_label = Text(size=(1, 20), pos=(2, 0), is_transparent=True)

        def on_damping(value):
            fluid.damping = 1 - value
            damp_label.add_str(f"Damping: {value:.2f}".center(20))

        damping = Slider(
            min=0.0,
            max=0.2,
            start_value=0.01,
            callback=on_damping,
            size=(1, 20),
            pos=(3, 0),
            is_transparent=True,
            alpha=0.0,
        )

        self.add_gadgets(
            fluid,
            smooth_toggle,
            binary_toggle,
            momentum_toggle,
            pressure_toggle,
            damp_label,
            damping,
        )


if __name__ == "__main__":
    NavierStokesApp(title="Fluid Simulation").run()
