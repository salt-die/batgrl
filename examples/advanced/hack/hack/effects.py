import asyncio

import numpy as np

from nurses_2.widgets.widget import Widget

from .colors import BRIGHT_COLOR_PAIR

CRT_LEN = 22 * 53
PS = np.linspace(0.99, 0, CRT_LEN)[..., None] ** 0.5
NPS = (1 - PS) * BRIGHT_COLOR_PAIR
NPS_2 = (1 - PS) * BRIGHT_COLOR_PAIR.reversed()
SKIP = 23  # Increase for a faster scanline.


class Darken(Widget):
    """
    Darken view.
    """

    def render(self, canvas, colors):
        super().render(canvas, colors)
        for rect in self.region.rects():
            colors[rect.to_slices()] >>= 1


class BOLDCRT(Widget):
    """
    Bold all text and apply a crt effect.
    """

    def on_add(self):
        super().on_add()
        self._i = 0
        self._crt_task = asyncio.create_task(self._crt_effect())

    def on_remove(self):
        self._crt_task.cancel()
        super().on_remove()

    async def _crt_effect(self):
        while True:
            y, x = self.size
            self._i += SKIP
            self._i %= y * x
            await asyncio.sleep(0)

    def render(self, canvas, colors):
        py, px = self.absolute_pos
        h, w = self.size

        dst = slice(py, py + h), slice(px, px + w)
        canvas[dst]["bold"] = True

        y, x = divmod(self._i, w)
        nchars = 0
        while nchars < CRT_LEN:
            strip = colors[dst][y, x : x + CRT_LEN - nchars]
            end = nchars + len(strip)

            normal = (strip * PS[nchars:end] + NPS[nchars:end]).astype(np.uint8)
            reversed = (strip * PS[nchars:end] + NPS_2[nchars:end]).astype(np.uint8)
            where_reversed = strip[:, :3].sum(axis=-1) < strip[:, 3:].sum(axis=-1)
            strip[:] = normal
            strip[where_reversed] = reversed[where_reversed]

            nchars = end
            y = (y + 1) % h
            x = 0
