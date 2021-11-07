"""
Click to add fluid. `r` to reset.
"""
import numpy as np
import cv2
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
        """
        Resize widget.
        """
        h, w = size
        gsize = 2 * h + 4, w + 4

        self.pressure = np.zeros(gsize, dtype=float)
        self.momentum = np.zeros(gsize, dtype=float)

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

        self.momentum = (
            filter2D(momentum, -1, DIFFUSION, borderType=cv2.BORDER_REFLECT)
            + filter2D(pressure, -1, CONVECTION, borderType=cv2.BORDER_REFLECT)
        )

        delta = filter2D(self.momentum, -1, POISSON, borderType=cv2.BORDER_REFLECT)

        self.pressure = (
            filter2D(pressure, -1, POISSON, borderType=cv2.BORDER_REFLECT)
            + .5 * (delta - delta**2)
        )

        self.texture[..., :3] = (sigmoid(self.pressure[2: -2, 2: -2, None]) * WATER_COLOR).astype(int)

        super().render(canvas_view, colors_view, rect)


class FluidApp(App):
    async def on_start(self):
        self.root.add_widget(Fluid())


FluidApp().run()
