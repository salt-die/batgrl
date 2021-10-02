from pathlib import Path

import cv2
import numpy as np

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


class BrailleImage(Widget):
    """
    An image painted with braille unicode characters.

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
        h, w = self.size

        img = cv2.imread(str(self.path), cv2.IMREAD_COLOR)
        img_bgr = cv2.resize(img, (2 * w, 4 * h))

        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        img_hls = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HLS)

        rgb_sectioned = np.swapaxes(img_rgb.reshape(h, 4, w, 2, 3), 1, 2)
        hls_sectioned = np.swapaxes(img_hls.reshape(h, 4, w, 2, 3), 1, 2)

        # First, find the average lightness of each 4x2 section of the image (`average_lightness`).
        # Braille dots are placed wherever the lightness is greater than `average_lightness`.
        # The background color will be the average of the colors darker than `average_lightness`.
        # The foreground color will be the average of the colors lighter than `average_lightness`.

        lightness = hls_sectioned[..., 1]
        average_lightness = np.average(lightness, axis=(2, 3))
        where_dots = lightness > average_lightness[..., None, None]

        # `ords` is an array of braille character ordinals created from `where_dots`.
        ords = np.sum(
            where_dots * _TO_BIN,
            axis=(2, 3),
            initial=0x2800,  # first braille ord
            dtype=np.uint16,
        )
        self.canvas = vectorized_chr(ords)

        ndots = where_dots.sum(axis=(2, 3))
        ndots_neg = 8 - ndots

        background = rgb_sectioned.copy()
        background[where_dots] = 0
        bg = background.sum(axis=(2, 3)) / ndots_neg[..., None]

        foreground = rgb_sectioned.copy()
        foreground[~where_dots] = 0
        fg = foreground.sum(axis=(2, 3)) / ndots[..., None]

        fixed_bg = np.where(np.isin(bg, (np.nan, np.inf)), fg, bg).astype(np.uint8)
        fixed_fg = np.where(np.isin(fg, (np.nan, np.inf)), bg, fg).astype(np.uint8)

        self.colors[..., :3] = fixed_bg
        self.colors[..., 3:] = fixed_fg
