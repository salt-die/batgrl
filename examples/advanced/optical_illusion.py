import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.graphic_widget import GraphicWidget, composite
from nurses_2.colors import AColor

LEN = 20
COLORS = AColor.from_hex("6d42b2"), AColor.from_hex("9c42b2")
DARK = np.zeros((6, 6, 4), np.uint8)
DARK[:, 2:4] = DARK[2:4, :] = AColor.from_hex("200d4c")
LIGHT = np.zeros_like(DARK)
LIGHT[:, 2:4] = LIGHT[2:4, :] = AColor.from_hex("b24290")
PATTERN = LIGHT, LIGHT, DARK, LIGHT, DARK, DARK, LIGHT, DARK
NCHECKS = len(PATTERN)

class IllusionApp(App):
    async def on_start(self):
        illusion = GraphicWidget(size=(NCHECKS * LEN // 2, NCHECKS * LEN))

        for y in range(NCHECKS + 1):
            for x in range(NCHECKS + 1):
                illusion.texture[y * LEN: (y + 1) * LEN, x * LEN: (x + 1) * LEN] = COLORS[(x + y) % 2]
                composite(PATTERN[(x - y) % NCHECKS], illusion.texture, (y * LEN - 3, x * LEN - 3))

        self.add_widget(illusion)
        while True:
            await asyncio.sleep(0)
            illusion.texture = np.roll(illusion.texture, 1, 0)

IllusionApp(title="Optical Illusion").run()
