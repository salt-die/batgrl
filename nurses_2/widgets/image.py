from pathlib import Path

import cv2
import numpy as np

from .widget import Widget
from ..colors import BLACK_ON_BLACK


class Image(Widget):
    """
    An Image widget.

    Parameters
    ----------
    path : pathlib.Path
        Path to image.
    is_grayscale : bool, default: False
        If true, convert image to grayscale.
    alpha_threshold : int, default: 0
        If Image is transparent and its texture has an alpha channel, alpha
        values less than or equal to alpha_threshold will be considered
        fully transparent. (0 <= alpha_threshold <= 255)
    """
    def __init__(self, *args, path: Path, is_grayscale=False, alpha_threshold=0, **kwargs):
        kwargs.pop('default_char', None)
        kwargs.pop('default_color', None)

        super().__init__(*args, default_char="▀", default_color=BLACK_ON_BLACK, **kwargs)

        self.path = path
        self.is_grayscale = is_grayscale
        self.alpha_threshold = alpha_threshold

        # Determine if there's an alpha channel
        unchanged_texture = cv2.imread(str(path), cv2.IMREAD_UNCHANGED)

        if unchanged_texture.shape[-1] == 4:
            self.alpha = unchanged_texture[:, :, -1].copy()
        else:
            self.alpha = None

        # Reload, but ensure format.
        self.texture = cv2.cvtColor(cv2.imread(str(path), cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB)

        self.resize(self.dim)

    def resize(self, dim):
        """
        Resize image.
        """
        h, w = dim
        TEXTURE_DIM = w, 2 * h

        self.canvas = np.full(dim, self.default_char, dtype=object)
        self.colors = np.zeros((h, w, 6), dtype=np.uint8)

        if self.alpha is not None and self.is_transparent:
            alpha = cv2.resize(self.alpha, TEXTURE_DIM)
            transparent = alpha <= self.alpha_threshold

            self.canvas[transparent[::2] & transparent[1::2]] = " "

        texture =  cv2.resize(self.texture, TEXTURE_DIM)
        self.colors[:, :, :3] = texture[::2]
        self.colors[:, :, 3:] = texture[1::2]

        for child in self.children:
            child.update_geometry()
