import numpy as np

from ..clamp import clamp
from ..colors import gradient, ColorPair
from .behaviors.themable import Themable
from .text_widget import TextWidget

FULL_BLOCK = "█"
VERTICAL_BLOCKS = " ▁▂▃▄▅▆▇"
HORIZONTAL_BLOCKS = " ▏▎▍▌▋▊▉"
GRAD_LEN = 7


class ProgressBar(Themable, TextWidget):
    """
    A progress bar widget.

    Parameters
    ----------
    is_horizontal : bool, default: True
        If true, the bar will progress to the right, else
        the bar will progress upwards.

    Notes
    -----
    Set the `progress` property to a value between `0.0`
    and `1.0` to update the bar.
    """
    def __init__(self, is_horizontal: bool=True, **kwargs):
        super().__init__(**kwargs)

        self._is_horizontal = is_horizontal
        self._progress = 0.0

        self.update_theme()

    @property
    def progress(self) -> float:
        return self._progress

    @progress.setter
    def progress(self, progress: float):
        self._progress = clamp(progress, 0.0, 1.0)
        self._update_canvas()

    @property
    def is_horizontal(self) -> bool:
        return self._is_horizontal

    @is_horizontal.setter
    def is_horizontal(self, is_horizontal: bool):
        self._is_horizontal = is_horizontal
        self._update_canvas()

    def resize(self, size):
        super().resize(size)
        self._update_canvas()

    def update_theme(self):
        self._fill = ColorPair.from_colors(
            self.color_theme.secondary_bg,
            self.color_theme.primary_bg,
        )

        self._head = np.array(
            gradient(
                self.color_theme.primary_color_pair,
                self._fill,
                GRAD_LEN,
            )
        )

        self._update_canvas()

    def _update_canvas(self):
        if self.is_horizontal:
            fill, partial = divmod(self.progress * self.width, 1)
            fill_length, partial_index = int(fill), int(len(HORIZONTAL_BLOCKS) * partial)
            self.canvas[:, :fill_length] = FULL_BLOCK
            self.colors[:] = self._fill

            if fill_length < self.width:
                self.canvas[:, fill_length] = HORIZONTAL_BLOCKS[partial_index]
                self.canvas[:, fill_length + 1:] = HORIZONTAL_BLOCKS[0]

                if fill_length + 1 <= GRAD_LEN:
                    self.colors[:, fill_length::-1] = self._head[:fill_length + 1]
                else:
                    self.colors[:, fill_length:fill_length - GRAD_LEN:-1] = self._head
            else:
                if self.width <= GRAD_LEN:
                    self.colors[:, ::-1] = self._head[:self.width]
                else:
                    self.colors[:, :-GRAD_LEN - 1:-1] = self._head

        else:
            fill, partial = divmod(self.progress * self.height, 1)
            fill_length, partial_index = int(fill), int(len(VERTICAL_BLOCKS) * partial)
            canvas = self.canvas[::-1]
            canvas[:fill_length] = FULL_BLOCK
            colors = self.colors[::-1]
            colors[:] = self._fill

            if fill_length < self.height:
                canvas[fill_length: fill_length + 1] = VERTICAL_BLOCKS[partial_index]
                canvas[fill_length + 1:] = VERTICAL_BLOCKS[0]

                if fill_length + 1 <= GRAD_LEN:
                    colors[fill_length::-1] = self._head[:fill_length + 1, None]
                else:
                    colors[fill_length:fill_length - GRAD_LEN:-1] = self._head[:, None]
            else:
                if self.height <= GRAD_LEN:
                    colors[::-1] = self._head[:self.height, None]
                else:
                    colors[:-GRAD_LEN - 1:-1] = self._head[:, None]
