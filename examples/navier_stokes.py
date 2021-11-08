"""
Click to add fluid. `r` to reset.

`cv2` convolutions (`filter2D`) currently don't support boundary wrapping. This is done manually by creating
pressure and momentum arrays equal to the widget's texture plus a 2-width border and copying data into that border.

This simulates discrete Navier-Stokes with 0 viscosity and a rho of 1. Note that using DIFFUSION kernel instead of
POISSON kernel (for the convolutions that used POISSON) will achieve almost identical results.

An alternative (read: *possibly better*) visualization is to copy the derivative of the pressure array into the
widget's texture instead. This can be approximated by taking the difference of current pressure and previous pressure.
"""
import numpy as np
from cv2 import filter2D

from nurses_2.app import App
from nurses_2.colors import Color
from nurses_2.io import MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.behaviors import AutoSizeBehavior

# Kernels
CONVECTION = np.array([
    [   0, .25,    0],
    [ .25,  -1,  .25],
    [   0, .25,    0],
])
DIFFUSION = np.array([
    [.025,  .1, .025],
    [  .1,  .5,   .1],
    [.025,  .1, .025],
])
POISSON = np.array([
    [   0, .25,    0],
    [ .25,   0,  .25],
    [   0, .25,    0],
])

WATER_COLOR = Color.from_hex("1259FF")

def wrap_border(array):
    array[:2] = array[-4: -2][::-1]
    array[-2:] = array[2: 4][::-1]
    array[2: -2, :2] = array[2: -2, -4: -2][::-1]
    array[2: -2, -2:] = array[2: -2, 2: 4][::-1]

def sigmoid(array):
    return 1 / (1 + np.e**-array)


class Fluid(AutoSizeBehavior, GraphicWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resize(self.size)

    def resize(self, size):
        size_with_border = 2 * size.height + 4, size.width + 4

        self.pressure = np.zeros(size_with_border, dtype=float)
        self.momentum = np.zeros(size_with_border, dtype=float)

        super().resize(size)

    def on_click(self, mouse_event):
        if not self.collides_coords(mouse_event.position):
            return False

        if mouse_event.button is not MouseButton.NO_BUTTON:
            y, x = self.absolute_to_relative_coords(mouse_event.position)

            Y = 2 * y + 2

            self.pressure[Y: Y + 2, x + 2: x + 4] += 2.0

            return True

    def on_press(self, key_press_event):
        if key_press_event.key in ("r", "R"):
            self.resize(self.size)  # Reset
            return True

    def render(self, canvas_view, colors_view, rect):
        pressure = self.pressure
        momentum = self.momentum

        wrap_border(momentum)
        wrap_border(pressure)

        self.momentum = filter2D(momentum, -1, DIFFUSION) + filter2D(pressure, -1, CONVECTION)

        delta = filter2D(self.momentum, -1, POISSON)

        self.pressure = filter2D(pressure, -1, POISSON) + .5 * (delta - delta**2)

        self.texture[..., :3] = (sigmoid(self.pressure[2: -2, 2: -2, None]) * WATER_COLOR).astype(int)

        super().render(canvas_view, colors_view, rect)


class FluidApp(App):
    async def on_start(self):
        self.root.add_widget(Fluid())


FluidApp().run()
