import cv2
import numpy as np

from ..data_structures import Size
from ._binary_to_braille import binary_to_braille
from .text_widget import TextWidget

# TODO:
# * Ticks
# * Labels
# * Multiple plots (similar functionality can be achieved by setting the plots to be transparent and layering them)
# * Legend
# * Embed in scroll view?
# * Zoomable?
class Plot2D(TextWidget):
    """
    A 2-D plot widget.

    Parameters
    ----------
    xs : list[float] | np.ndarray
        x-values of points to plot.
    ys : list[float] | np.ndarray
        y-values of points to plot.
    xmin : float | None, default: None
        Minimum x-value of plot. If None, xmin will be min(xs).
    xmax : float | None, default: None
        Maximum x-value of plot. If None, xmax will be max(xs).
    ymin : float | None, default: None
        Minimum y-value of plot. If None, ymin will be min(ys).
    ymax : float | None, default: None
        Maximum y-value of plot. If None, ymax will be max(ys).
    """
    def __init__(
        self,
        xs: list[float] | np.ndarray,
        ys: list[float] | np.ndarray,
        *,
        xmin: float | None=None,
        xmax: float | None=None,
        ymin: float | None=None,
        ymax: float | None=None,
        **kwargs,
    ):
        super().__init__(**kwargs)

        self._xs = np.array(xs, dtype=float)
        self._ys = np.array(ys, dtype=float)

        self.xmin = self._xs.min() if xmin is None else xmin
        self.xmax = self._xs.max() if xmax is None else xmax
        self.ymin = self._ys.min() if ymin is None else ymin
        self.ymax = self._ys.max() if ymax is None else ymax

        self.resize(self.size)

    def resize(self, size: Size):
        h, w = size
        self._size = Size(h, w)
        h4 = h * 4
        w2 = w * 2

        ys = self._ys
        xs = self._xs

        scaled_ys = h4 - h4 * (ys - self.ymin) / (self.ymax - self.ymin)
        scaled_xs = w2 * (xs - self.xmin) / (self.xmax - self.xmin)
        coords = np.dstack((scaled_xs, scaled_ys)).astype(int)

        plot = np.zeros((h4, w2), dtype=int)
        cv2.polylines(plot, coords, isClosed=False, color=1)

        sectioned = np.swapaxes(plot.reshape(h, 4, w, 2), 1, 2)

        self.canvas = binary_to_braille(sectioned)
        self.colors = np.full((*size, 6), self.default_color_pair, dtype=np.uint8)

        for child in self.children:
            child.update_geometry()
