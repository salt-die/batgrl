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


class BouncingWidget(Widget):
    def __init__(self, dim, velocity):
        super().__init__(dim)
        self.velocity = velocity

    def start(self, roll_axis):
        asyncio.create_task(self.bounce())
        asyncio.create_task(self.roll(roll_axis))

    async def bounce(self):
        velocity = self.velocity
        velocity /= abs(velocity)

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
            self.content = np.roll(self.content, 1, (axis, ))
            self.attrs = np.roll(self.attrs, 1, (axis, ))

            await asyncio.sleep(.11)


class MyApp(App):
    async def on_start(self):
        self.key_bindings.add('escape')(self.exit)

        root = self.root

        colors = cycle((ORANGE, YELLOW))
        some_text = cycle('NURSES!')

        widget_1 = BouncingWidget(dim=(20, 20), velocity=1 + 1j)
        widget_2 = BouncingWidget(dim=(10, 30), velocity=-1 - 1j)

        # Fill widget content.
        for i in range(20):
            for j in range(20):
                widget_1.content[i, j] = next(some_text)
                widget_1.attrs[i, j] = next(colors)

        for i in range(10):
            for j in range(30):
                widget_2.content[i, j] = next(some_text)
                widget_2.attrs[i, j] = next(colors)

        root.add_widget(widget_1)
        root.add_widget(widget_2)

        widget_1.start(roll_axis=0)
        widget_2.start(roll_axis=1)


MyApp().run()
