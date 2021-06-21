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


class MyApp(App):
    def build(self):
        self.kb.add('escape')(lambda event: self.exit())

        colors = cycle((RED, BLUE))
        some_text = cycle('NURSES!')

        panel_one = Panel((20, 20))

        for i in range(20):
            for j in range(20):
                panel_one.content[i, j] = next(some_text)
                panel_one.attrs[i, j] = next(colors)

        panel_two = Panel((10, 30))

        for i in range(10):
            for j in range(30):
                panel_two.content[i, j] = next(some_text)
                panel_two.attrs[i, j] = next(colors)

        self.screen.panels.extend((panel_one, panel_two))

    async def on_start(self):
        panel_one, panel_two = self.screen.panels
        h, w = self.screen.dim

        while True:
            panel_one.content = np.roll(panel_one.content, 1, (0, ))
            panel_one.attrs = np.roll(panel_one.attrs, 1, (0, ))
            panel_one.top = (panel_one.top + 1) % h

            panel_two.content = np.roll(panel_two.content, 1, (1, ))
            panel_two.attrs = np.roll(panel_two.attrs, 1, (1, ))
            panel_two.left = (panel_two.left + 1) % w

            await asyncio.sleep(.05)

MyApp().run()
