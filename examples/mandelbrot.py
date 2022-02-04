import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.graphic_widget import GraphicWidget, Size

LEFT, RIGHT = -2.0, 1.0
BOTTOM, TOP = -1.5, 1.5
NTHETAS = 200
ITERATIONS = 48

PALETTE = np.array([
    [  66,  30,  15, 255],
    [  25,   7,  26, 255],
    [   9,   1,  47, 255],
    [   4,   4,  73, 255],
    [   0,   7, 100, 255],
    [  12,  44, 138, 255],
    [  24,  82, 177, 255],
    [  57, 125, 209, 255],
    [ 134, 181, 229, 255],
    [ 211, 236, 248, 255],
    [ 241, 233, 291, 255],
    [ 255, 170,   0, 255],
    [ 204, 128,   0, 255],
    [ 153,  87,   0, 255],
    [ 106,  52,   3, 255],
    [   0,   0,   0, 255],
])

def spiral(theta):
    return np.e**(.1 * -theta) * (np.sin(theta) + np.cos(theta) * 1j)

def julia(theta, grid):
    Z = np.full_like(grid, spiral(theta))
    escapes = np.zeros_like(Z, dtype=int)

    for i in range(1, ITERATIONS):
        Z = np.where(escapes, 0, Z**2 + grid)
        escapes[np.abs(Z) > 2] = i

    return PALETTE[np.where(escapes, escapes % 16, -1)]


class Mandelbrot(GraphicWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._index = 0
        self.resize(self.size)
        asyncio.create_task(self._spiral())

    def resize(self, size: Size):
        h, w = size
        self._size = Size(h, w)

        ys = np.linspace(TOP, BOTTOM, 2 * h)
        xs = np.linspace(LEFT, RIGHT, w)

        xs, ys = np.meshgrid(xs, ys)
        grid = xs + ys * 1j
        thetas = np.linspace(-2 * np.pi, 6 * np.pi, NTHETAS >> 1)
        textures = [julia(theta, grid) for theta in thetas]
        self._textures = textures + textures[::-1]
        self.texture = self._textures[self._index]

    async def _spiral(self):
        while True:
            self._index += 1
            self._index %= NTHETAS
            self.texture = self._textures[self._index]

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

class MandelbrotApp(App):
    async def on_start(self):
        self.add_widget(Mandelbrot(size_hint=(1.0, 1.0)))


MandelbrotApp().run()
