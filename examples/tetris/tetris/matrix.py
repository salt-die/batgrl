import asyncio

import numpy as np

from nurses_2.widgets.behaviors.effects import Effect
from nurses_2.widgets.text_widget import TextWidget


class LevelGlowEffect(Effect):
    """
    Apply a glow effect that quickens as levels increase.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._glow = 0
        asyncio.create_task(self.glow())

    async def glow(self):
        while self.parent is None:
            await asyncio.sleep(0)

        while True:
            level = self.parent.level
            alpha = np.linspace(0, min(1, .05 * level), 30)

            brighten_delay = .04 * .8 ** level
            darken_delay = 2 * brighten_delay
            sleep = 20 * darken_delay

            for self._glow in alpha:
                await asyncio.sleep(brighten_delay)

            for self._glow in alpha[::-1]:
                await asyncio.sleep(darken_delay)

            await asyncio.sleep(sleep)

    def apply_effect(self, canvas_view, colors_view, source_slice: tuple[slice, slice]):
        alpha = self._glow

        visible = self.canvas[source_slice] != " "

        colors_view[..., :3][visible] = (colors_view[..., :3][visible] * (1 - alpha) + alpha * 255).astype(int)


class MatrixWidget(LevelGlowEffect, TextWidget):
    """
    Visual representation of tetromino matrix.
    """
