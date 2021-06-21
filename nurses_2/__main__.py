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

RED = Attrs(color='ff0000', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)
BLUE = Attrs(color='0000ff', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)


class MovingWidget(Widget):
    def __init__(self, dim, velocity):
        super().__init__(dim)
        self.velocity = velocity / abs(velocity)
        self.pos = self.top + self.left * 1j

    def update(self):
        self.pos += self.velocity

        self.top = int(self.pos.real)
        self.left = int(self.pos.imag)


class MyApp(App):
    def build(self):
        self.kb.add('escape')(lambda event: self.exit())

        colors = cycle((RED, BLUE))
        some_text = cycle('NURSES!')

        widget_1 = MovingWidget(dim=(20, 20), velocity=1 + 1j)

        for i in range(20):
            for j in range(20):
                widget_1.content[i, j] = next(some_text)
                widget_1.attrs[i, j] = next(colors)

        widget_2 = MovingWidget(dim=(10, 30), velocity=-1 - 1j)

        for i in range(10):
            for j in range(30):
                widget_2.content[i, j] = next(some_text)
                widget_2.attrs[i, j] = next(colors)

        self.root.add_widget(widget_1)
        self.root.add_widget(widget_2)

    async def on_start(self):
        root = self.root
        widgets = root.children
        widget_1, widget_2 = widgets

        async def bounce():
            while True:
                for widget in widgets:
                    widget.update()
                    if (
                        widget.top <= 0 and widget.velocity.real < 0
                        or widget.bottom > root.height and widget.velocity.real > 0
                    ):
                        widget.velocity = -widget.velocity.conjugate()

                    if (
                        widget.left <= 0 and widget.velocity.imag < 0
                        or widget.right > root.width and widget.velocity.imag > 0
                    ):
                        widget.velocity = widget.velocity.conjugate()

                await asyncio.sleep(.05)

        async def roll():
            while True:
                widget_1.content = np.roll(widget_1.content, 1, (0, ))
                widget_1.attrs = np.roll(widget_1.attrs, 1, (0, ))

                widget_2.content = np.roll(widget_2.content, 1, (1, ))
                widget_2.attrs = np.roll(widget_2.attrs, 1, (1, ))

                await asyncio.sleep(.11)

        await asyncio.gather(
            bounce(),
            roll(),
        )


MyApp().run()
