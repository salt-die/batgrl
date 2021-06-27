"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio

import numpy as np

from .app import App
from .widgets import Widget

ORANGE = 255, 140, 66, 108, 142, 173
YELLOW = 255, 242, 117, 108, 142, 173
TEAL = 10, 175, 170, 87, 10, 175
GREEN = 10, 175, 62, 87, 10, 175


class BouncingWidget(Widget):
    def start(self, velocity, roll_axis, palette):
        h, w = self.dim
        for i in range(h):
            for j in range(w):
                self.canvas[i, j] = 'NURSES!   '[(i + j) % 10]
                self.attrs[i, j] = palette[(i + j) % 2]

        asyncio.create_task(self.bounce(velocity))
        asyncio.create_task(self.roll(roll_axis))

    async def bounce(self, velocity):
        velocity /= abs(velocity)  # normalize

        pos = self.top + self.left * 1j
        root = self.root

        while True:
            pos += velocity

            self.top = top = int(pos.real)
            self.left = left = int(pos.imag)

            if (
                top <= 0 and velocity.real < 0
                or self.bottom > root.height and velocity.real > 0
            ):
                velocity = -velocity.conjugate()

            if (
                left <= 0 and velocity.imag < 0
                or self.right > root.width and velocity.imag > 0
            ):
                velocity = velocity.conjugate()

            await asyncio.sleep(.05)

    async def roll(self, axis):
        while True:
            self.canvas = np.roll(self.canvas, 1, (axis, ))
            self.attrs = np.roll(self.attrs, 1, (axis, ))

            await asyncio.sleep(.11)


class MyApp(App):
    async def on_start(self):
        self.key_bindings.add('escape')(self.exit)

        widget_1 = BouncingWidget(dim=(20, 20), is_transparent=True)
        widget_2 = BouncingWidget(dim=(10, 30), is_transparent=True)

        self.root.add_widgets(widget_1, widget_2)

        widget_1.start(velocity=1 + 1j, roll_axis=0, palette=(ORANGE, YELLOW))
        widget_2.start(velocity=-1 - 1j, roll_axis=1, palette=(TEAL, GREEN))


MyApp().run()
