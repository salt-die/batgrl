import asyncio

import numpy as np

from nurses_2.widgets.behaviors.effect import Effect
from nurses_2.widgets.widget import Widget

from .colors import BRIGHT_COLOR_PAIR

CRT_LEN = 22 * 53
PS = np.linspace(0.99, 0, CRT_LEN)[..., None]**.5
NPS = ((1 - PS) * BRIGHT_COLOR_PAIR)
NPS_2 = ((1 - PS) * BRIGHT_COLOR_PAIR.reversed())
SKIP = 23  # Increase for a faster scanline.


class Darken(Effect, Widget):
    """
    Darken view.
    """
    def apply_effect(self, canvas_view, colors_view, source):
        colors_view >>= 1


class BOLDCRT(Effect, Widget):
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

    def apply_effect(self, canvas_view, colors_view, source):
        canvas_view["bold"] = True

        h, w, _ = colors_view.shape
        y, x = divmod(self._i, w)
        nchars = 0
        while nchars < CRT_LEN:
            strip = colors_view[y, x: x + CRT_LEN - nchars]
            lstrip = len(strip)
            end = nchars + lstrip

            normal = (strip * PS[nchars: end] + NPS[nchars: end]).astype(np.uint8)
            reversed = (strip * PS[nchars: end] + NPS_2[nchars: end]).astype(np.uint8)
            where_reversed = strip[:, :3].sum(axis=-1) < strip[:, 3:].sum(axis=-1)
            strip[:] = normal
            strip[where_reversed] = reversed[where_reversed]

            nchars = end
            y = (y + 1) % h
            x = 0
