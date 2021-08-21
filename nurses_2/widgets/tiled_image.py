from math import ceil

import numpy as np

from .widget import Widget
from .image import Image


class TiledImage(Widget):
    """
    A widget tiled with an image. The widget's size will be extended so that there are no partial tiles.

    Parameters
    ----------
    tile : Image
        The image widget that will be tiled.
    """
    def __init__(self, *args, tile: Image, is_transparent=True, **kwargs):
        super().__init__(*args, is_transparent=is_transparent, **kwargs)

        self.tile = tile

        self.resize(self.size)

    def resize(self, size):
        """
        Resize widget. Size will be extended enough to fully paint all tiles.
        """
        min_height, min_width = size
        tile = self.tile

        vertical_repeat = ceil(min_height / tile.height)
        horizontal_repeat = ceil(min_width / tile.width)

        self._size = vertical_repeat * tile.height, horizontal_repeat * tile.width

        self.canvas = np.tile(tile.canvas, (vertical_repeat, horizontal_repeat))
        self.colors = np.tile(tile.colors, (vertical_repeat, horizontal_repeat, 1))
        self.alpha_channels = np.tile(tile.alpha_channels, (vertical_repeat, horizontal_repeat, 1, 1))

        for child in self.children:
            child.update_geometry()

    render = Image.render
