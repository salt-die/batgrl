import asyncio

import numpy as np
from batgrl.gadgets.graphics import Graphics
from batgrl.geometry import rect_slice


class MatrixGadget(Graphics):
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

    def _render(self, canvas):
        super()._render(canvas)
        glow = self._glow
        abs_pos = self.absolute_pos
        for pos, size in self._region.rects():
            dst_y, dst_x = rect_slice(pos, size)
            src_y, src_x = rect_slice(pos - abs_pos, size)

            visible = (
                self.texture[
                    2 * src_y.start : 2 * src_y.stop,
                    2 * src_x.start : 2 * src_x.stop,
                    3,
                ]
                == 255
            )
            fg = canvas["fg_color"][dst_y, dst_x]
            fg[visible[::2]] = (fg[visible[::2]] * (1 - glow) + glow * 255).astype(
                np.uint8
            )
            bg = canvas["bg_color"][dst_y, dst_x]
            bg[visible[1::2]] = (bg[visible[1::2]] * (1 - glow) + glow * 255).astype(
                np.uint8
            )
