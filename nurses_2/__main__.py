"""
For temporary testing.  This file will be removed.

`esc` to exit.

"""
import asyncio
from itertools import cycle

import numpy as np
from prompt_toolkit.styles import Attrs

from .app import App
from .panel import Panel

RED = Attrs(color='ff0000', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)
BLUE = Attrs(color='0000ff', bgcolor='', bold=False, underline=False, italic=False, blink=False, reverse=False, hidden=False)


class VelocityPanel(Panel):
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

        panel_one = VelocityPanel((20, 20), 1 + 1j)

        for i in range(20):
            for j in range(20):
                panel_one.content[i, j] = next(some_text)
                panel_one.attrs[i, j] = next(colors)

        panel_two = VelocityPanel((10, 30), 1 - 1j)

        for i in range(10):
            for j in range(30):
                panel_two.content[i, j] = next(some_text)
                panel_two.attrs[i, j] = next(colors)

        self.screen.panels.extend((panel_one, panel_two))

    async def on_start(self):
        screen = self.screen
        panel_one, panel_two = screen.panels

        async def bounce():
            while True:
                for panel in screen.panels:
                    panel.update()
                    if (
                        panel.top < 0 and panel.velocity.real < 0
                        or panel.bottom > screen.height and panel.velocity.real > 0
                    ):
                        panel.velocity = -panel.velocity.conjugate()

                    if (
                        panel.left < 0 and panel.velocity.imag < 0
                        or panel.right > screen.width and panel.velocity.imag > 0
                    ):
                        panel.velocity = panel.velocity.conjugate()

                await asyncio.sleep(.05)

        async def roll():
            while True:
                panel_one.content = np.roll(panel_one.content, 1, (0, ))
                panel_one.attrs = np.roll(panel_one.attrs, 1, (0, ))

                panel_two.content = np.roll(panel_two.content, 1, (1, ))
                panel_two.attrs = np.roll(panel_two.attrs, 1, (1, ))

                await asyncio.sleep(.11)

        await asyncio.gather(
            bounce(),
            roll(),
        )


MyApp().run()
