from typing import Sequence, Union

import numpy as np

from .widget import Widget
from .image import Image
from .tiled_image import TiledImage


class Parallax(Widget):
    """
    A parallax widget.

    Parameters
    ----------
    layers: Sequence[Union[Image, TiledImage]]
        Individual layers of the parallax in background-to-foreground order.
    speeds: Sequence[float]
        The scrolling speed of each individual layer. A speed of x will scroll a
        layer by `round(x * offset)` where offset is either `vertical_offset` or
        `horizontal_offset` of the parallax.
    """
    def __init__(self, *args, layers: Sequence[Union[Image, TiledImage]], speeds: Sequence[float], **kwargs):
        assert len(layers) == len(speeds), f"Inconsistent lengths of layers ({len(layers)}) and speeds ({len(speeds)})"

        super().__init__(*args, **kwargs)

        self.layers = layers

        self._image_copies = [layer.colors.copy() for layer in layers]
        self._alpha_copies = [layer.alpha_channels.copy() for layer in layers]

        self.speeds = speeds

        self._vertical_offset = self._horizontal_offset = 0

        for widget in layers:
            self.add_widget(widget)

    @property
    def vertical_offset(self):
        return self._vertical_offset

    @vertical_offset.setter
    def vertical_offset(self, offset):
        self._vertical_offset = offset
        self._adjust()

    @property
    def horizontal_offset(self):
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset):
        self._horizontal_offset = offset
        self._adjust()

    @property
    def offset(self):
        return self._vertical_offset, self._horizontal_offset

    @offset.setter
    def offset(self, offset):
        self._vertical_offset, self._horizontal_offset = offset
        self._adjust()

    def _adjust(self):
        for speed, image, alpha, layer in zip(
            self.speeds,
            self._image_copies,
            self._alpha_copies,
            self.layers
        ):
            rolls = -round(speed * self._vertical_offset), -round(speed * self._horizontal_offset)
            axis = 0, 1
            layer.colors = np.roll(image, rolls, axis)
            layer.alpha_channels = np.roll(alpha, rolls, axis)