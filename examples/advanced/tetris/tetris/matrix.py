import asyncio

import numpy as np

from nurses_2.widgets.graphic_widget import GraphicWidget


class MatrixWidget(GraphicWidget):
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

    def render(self, canvas, colors):
        super().render(canvas, colors)
        glow = self._glow
        abs_pos = self.absolute_pos
        for rect in self.region.rects():
            dst_y, dst_x = rect.to_slices()
            src_y, src_x = rect.to_slices(abs_pos)

            visible = (
                self.texture[
                    2 * src_y.start : 2 * src_y.stop,
                    2 * src_x.start : 2 * src_x.stop,
                    3,
                ]
                == 255
            )
            fg = colors[dst_y, dst_x, :3]
            fg[visible[::2]] = (fg[visible[::2]] * (1 - glow) + glow * 255).astype(
                np.uint8
            )
            bg = colors[dst_y, dst_x, 3:]
            bg[visible[1::2]] = (bg[visible[1::2]] * (1 - glow) + glow * 255).astype(
                np.uint8
            )
