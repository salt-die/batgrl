from pathlib import Path

import cv2
import numpy as np

from .graphic_widget import Interpolation
from .widget import Widget

_TO_BIN = np.array(
    [
        [ 1,   8],
        [ 2,  16],
        [ 4,  32],
        [64, 128],
    ],
    dtype=np.uint8,
)
_TO_BIN.flags.writeable = False

vectorized_chr = np.vectorize(chr)


class BrailleGraphicWidget(Widget):
    """
    A widget painted with braille unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    """
    def __init__(self, *args, path: Path, **kwargs):
        super().__init__(*args, **kwargs)
        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self._load_texture()

    def resize(self, size):
        super().resize(size)
        self._load_texture()

    def _load_texture(self):
        img = cv2.imread(str(self.path), cv2.IMREAD_COLOR)
        img_hls = cv2.cvtColor(img, cv2.COLOR_BGR2HLS)

        h, w = self.size
        img_resized = cv2.resize(img_hls, (2 * w, 4 * h))

        sectioned = np.swapaxes(img_resized.reshape(h, 4, w, 2, 3), 1, 2)

        lightness = sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_dots = lightness > average_lightness[..., None, None]

        ords = np.sum(
            where_dots * _TO_BIN,
            axis=(2, 3),
            initial=0x2800,  # first braille ord
            dtype=np.uint16,
        )
        self.canvas = vectorized_chr(ords)

        # TODO: Probably describe what's going on here...
        # TODO: Background needs to be weighted more than foreground.
        ndots = where_dots.sum(axis=(2, 3))
        ndots_neg = 8 - ndots

        background = sectioned.copy()
        background[where_dots] = 0
        bg = background.sum(axis=(2, 3)) / ndots_neg[..., None]

        foreground = sectioned.copy()
        foreground[~where_dots] = 0
        fg = foreground.sum(axis=(2, 3)) / ndots[..., None]

        fixed_bg = np.where(~np.isin(bg, (np.nan, np.inf)), bg, fg).astype(np.uint8)
        fixed_fg = np.where(~np.isin(fg, (np.nan, np.inf)), fg, bg).astype(np.uint8)

        self.colors[..., :3] = cv2.cvtColor(fixed_fg, cv2.COLOR_HLS2RGB)
        self.colors[..., 3:] = cv2.cvtColor(fixed_bg, cv2.COLOR_HLS2RGB)
