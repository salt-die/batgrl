import numpy as np
from batgrl.gadgets.gadget import Gadget


class Darken(Gadget):
    """Darken view."""

    def _render(self, canvas):
        super()._render(canvas)
        for rect in self.region.rects():
            s = rect.to_slices()
            canvas["fg_color"][s] >>= 1
            canvas["bg_color"][s] >>= 1


class BOLDCRT(Gadget):
    """Bold all text and apply a crt effect."""

    def on_add(self):
        super().on_add()
        self._i = 0
        self.pct = np.ones((*self.size, 1), float)

    def _render(self, canvas):
        py, px = self.absolute_pos
        h, w = self.size
        size = h * w

        self.pct *= 0.9995
        for _ in range(20):
            y, x = divmod(self._i, w)

            dst = slice(py, py + h), slice(px, px + w)
            canvas[dst]["bold"] = True

            self.pct[y, x] = 1
            canvas["fg_color"][dst] = (canvas["fg_color"][dst] * self.pct).astype(
                np.uint8
            )
            canvas["bg_color"][dst] = (canvas["bg_color"][dst] * self.pct).astype(
                np.uint8
            )
            self._i += 1
            self._i %= size
