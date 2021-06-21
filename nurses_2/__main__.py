"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio
from itertools import cycle

import numpy as np
from prompt_toolkit.styles import Attrs

from .app import App
from .widgets import Widget

ORANGE = Attrs(color='FF8C42', bgcolor='6C8EAD', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)
YELLOW = Attrs(color='FFF275', bgcolor='6C8EAD', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)
COLORS = cycle((ORANGE, YELLOW))
TEXT = cycle('NURSES!')

class BouncingWidget(Widget):
    def start(self, velocity, roll_axis):
        h, w = self.dim
        for i in range(h):
            for j in range(w):
                self.canvas[i, j] = next(TEXT)
                self.attrs[i, j] = next(COLORS)

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

        widget_1 = BouncingWidget(dim=(20, 20))
        widget_2 = BouncingWidget(dim=(10, 30))

        self.root.add_widgets(widget_1, widget_2)

        widget_1.start(velocity=1 + 1j, roll_axis=0)
        widget_2.start(velocity=-1 -1j, roll_axis=1)


MyApp().run()
