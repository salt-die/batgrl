import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.graphic_widget import GraphicWidget, composite
from nurses_2.colors import AColor

H, W, LEN = 160, 160, 20

BG_COLOR = AColor.from_hex("6d42b2")
FG_COLOR = AColor.from_hex("9c42b2")

DARK = np.zeros((6, 6, 4), np.uint8)
DARK[:, 2:4] = DARK[2:4, :] = AColor.from_hex("200d4c")

LIGHT = np.zeros_like(DARK)
LIGHT[:, 2:4] = LIGHT[2:4, :] = AColor.from_hex("b24290")

PATTERN = [LIGHT, LIGHT, DARK, LIGHT, DARK, DARK, LIGHT, DARK]

class IllusionApp(App):
    async def on_start(self):
        illusion = GraphicWidget(size=(H // 2, W), default_color=BG_COLOR)

        rows = H // LEN
        cols = W // LEN
        for y in range(rows):
            for x in range(cols):
                if (y + x) % 2 == 0:
                    illusion.texture[y * LEN: (y + 1) * LEN, x * LEN: (x + 1) * LEN] = FG_COLOR

        for y in range(rows + 1):
            for x in range(cols + 1):
                cross = PATTERN[(x - y) % len(PATTERN)]
                composite(cross, illusion.texture, (y * LEN - 3, x * LEN - 3))

        self.add_widget(illusion)
        while True:
            await asyncio.sleep(0)
            illusion.texture = np.roll(illusion.texture, 1, 0)

IllusionApp(title="Optical Illusion").run()