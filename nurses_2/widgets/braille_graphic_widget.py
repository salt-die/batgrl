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

def texture_to_braille(arr):
    """
    Convert a `(m, n)`-shaped texture array to a `(m // 4, n // 2)`-shaped
    array of braille characters.

    Example
    -------
           In            -->           Out
    [0 1 0 1 1 0 1 0]           ['⢸' '⠺' '⡅' '⢵']
    [0 1 1 1 0 0 0 1]           ['⡄' '⡾' '⢜' '⠠']
    [0 1 0 1 1 0 1 1]
    [0 1 0 0 1 0 0 1]
    [0 0 0 1 0 1 0 0]
    [0 0 1 1 0 1 0 0]
    [1 0 1 1 1 0 0 1]
    [1 0 1 0 0 1 0 0]
    """
    h, w = arr.shape

    sectioned = np.swapaxes(arr.reshape(h // 4, 4, w // 2, 2), 1, 2)

    ords = np.sum(
        sectioned * _TO_BIN,
        axis=(2, 3),
        initial=0x2800,  # first braille ord
        dtype=np.uint16,
    )

    return vectorized_chr(ords)


class BrailleGraphicWidget(Widget):
    """
    A widget painted with braille unicode characters.

    Parameters
    ----------
    interpolation : Interpolation, default: Interpolation.LINEAR
        The interpolation used when resizing the widget's texture.
    auto_apply_texture : bool, default: False
        If true, `apply_texture` is called on every render.

    Notes
    -----
    BrailleGraphicWidgets have an underlying boolean array, `texture`. This texture can be
    applied to the canvas using the `apply_texture` method. Which converts 4x2 rectangular slices
    of the texture into corresponding braille characters. (The texture will be 4x the widget's height
    and 2x the widget's width.)

    Resizing resets `colors` to `default_color_pair`.
    """
    def __init__(
        self,
        *args,
        interpolation=Interpolation.LINEAR,
        auto_apply_texture=False,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        h, w = self.size
        self.texture = np.zeros((4 * h, 2 * w), dtype=np.uint8)
        self.interpolation = interpolation
        self.auto_apply_texture = auto_apply_texture

    def resize(self, size):
        self._size = h, w = size

        self.colors = np.full(
            (*size, 6),
            self.default_color_pair,
            dtype=np.uint8,
        )

        self.texture = cv2.resize(
            self.texture,
            (2 * w, 4 * h),
            interpolation=self.interpolation,
        )

        self.apply_texture()

    def apply_texture(self):
        """
        Paint texture to canvas.
        """
        self.canvas = texture_to_braille(self.texture)

    def load_texture(self, path: Path):
        """
        Load texture from path and paint to canvas.
        """
        img_grey = cv2.imread(str(path), cv2.IMREAD_GRAYSCALE)
        _, img_binary = cv2.threshold(img_grey, 255 >> 1, 1, cv2.THRESH_BINARY)

        h, w = self.size
        self.texture = cv2.resize(img_binary, (2 * w, 4 * h))
        self.apply_texture()

    def render(self, canvas_view, colors_view, rect):
        if self.auto_apply_texture:
            self.apply_texture()

        super().render(canvas_view, colors_view, rect)
