import numpy as np
from batgrl.gadgets.gadget import Gadget
from batgrl.geometry import rect_slice
from batgrl.text_tools import Style


class Darken(Gadget):
    """Darken view."""

    def _render(self, cells, graphics, kind):
        super()._render(cells, graphics, kind)
        for pos, size in self._region.rects():
            s = rect_slice(pos, size)
            cells["fg_color"][s] >>= 1
            cells["bg_color"][s] >>= 1


class BOLDCRT(Gadget):
    """Bold all text and apply a crt effect."""

    def on_add(self):
        super().on_add()
        self._i = 0
        self.pct = np.ones((*self.size, 1), float)

    def _render(self, cells, graphics, kind):
        py, px = self.absolute_pos
        h, w = self.size
        size = h * w

        self.pct *= 0.9995
        for _ in range(20):
            y, x = divmod(self._i, w)

            dst = slice(py, py + h), slice(px, px + w)
            cells[dst]["style"] |= Style.BOLD

            self.pct[y, x] = 1
            cells["fg_color"][dst] = (cells["fg_color"][dst] * self.pct).astype(
                np.uint8
            )
            cells["bg_color"][dst] = (cells["bg_color"][dst] * self.pct).astype(
                np.uint8
            )
            self._i += 1
            self._i %= size
