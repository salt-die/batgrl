import asyncio

import numpy as np

from nurses_2.widgets.behaviors.effect import Effect
from nurses_2.widgets.graphic_widget import GraphicWidget


class MatrixWidget(Effect, GraphicWidget):
    def on_add(self):
        super().on_add()
        self._glow = 0
        self._glow_task = asyncio.create_task(self.glow())

    def on_remove(self):
        super().on_remove()
        self._glow_task.cancel()

    async def glow(self):
        while self.parent is None:
            await asyncio.sleep(0)

        while True:
            level = self.parent.level
            glow = np.linspace(0, min(1, 0.05 * level), 30)

            brighten_delay = 0.04 * 0.8**level
            darken_delay = 2 * brighten_delay
            sleep = 20 * darken_delay

            for self._glow in glow:
                await asyncio.sleep(brighten_delay)

            for self._glow in glow[::-1]:
                await asyncio.sleep(darken_delay)

            await asyncio.sleep(sleep)

    def apply_effect(self, canvas_view, colors_view, source: tuple[slice, slice]):
        glow = self._glow
        visible = self.texture[..., 3] == 255
        colors_view[..., :3][visible[::2]] = (
            colors_view[..., :3][visible[::2]] * (1 - glow) + glow * 255
        ).astype(int)
        colors_view[..., 3:][visible[1::2]] = (
            colors_view[..., 3:][visible[1::2]] * (1 - glow) + glow * 255
        ).astype(int)
