from pathlib import Path

import cv2
import numpy as np

from ._binary_to_braille import binary_to_braille
from .text_widget import TextWidget


class BrailleImage(TextWidget):
    """
    An image painted with braille unicode characters.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    """
    def __init__(self, *, path: Path, **kwargs):
        super().__init__(**kwargs)
        self.path = path

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value
        self._load_texture()

    def on_size(self):
        h, w = self._size

        self.canvas = np.full((h, w), self.default_char, dtype=object)
        self.colors = np.full((h, w, 6), self.default_color_pair, dtype=np.uint8)

        self._load_texture()

    def _load_texture(self):
        h, w = self.size

        img = cv2.imread(str(self.path.absolute()), cv2.IMREAD_COLOR)
        img_bgr = cv2.resize(img, (2 * w, 4 * h))

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 4, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 4, w, 2, 3), 1, 2)

        # First, find the average lightness of each 4x2 section of the image (`average_lightness`).
        # Braille dots are placed where the lightness is greater than `average_lightness`.
        # The background color will be the average of the colors darker than `average_lightness`.
        # The foreground color will be the average of the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_dots = lightness > average_lightness[..., None, None]

        self.canvas = binary_to_braille(where_dots)

        ndots = where_dots.sum(axis=(2, 3))
        ndots_neg = 8 - ndots

        background = rgb_sectioned.copy()
        background[where_dots] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            bg = background.sum(axis=(2, 3)) / ndots_neg[..., None]  # average of colors darker than `average_lightness`

        foreground = rgb_sectioned.copy()
        foreground[~where_dots] = 0
        with np.errstate(divide="ignore", invalid="ignore"):
            fg = foreground.sum(axis=(2, 3)) / ndots[..., None]  # average of colors lighter than `average_lightness`

        self.colors[..., :3] = np.where(np.isin(fg, (np.nan, np.inf)), bg, fg)
        self.colors[..., 3:] = np.where(np.isin(bg, (np.nan, np.inf)), fg, bg)
