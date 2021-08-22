from math import ceil

import numpy as np

from .widget import Widget
from .image import Image


class ResizeProperty:
    def __set_name__(self, owner, name):
        self.name = "_" + name

    def __get__(self, instance, owner):
        if instance is None:
            return self

        return getattr(instance, self.name)

    def __set__(self, instance, value):
        instance.__dict__[self.name] = value
        instance.resize(instance.size)


class TiledImage(Widget):
    """
    A tiled image.

    Notes
    -----
    Updating the following properties immediately reloads the tiled widget:
        * tile
        * allow_partial_tiling

    Parameters
    ----------
    tile : Image
        The image widget that will used to tile.
    allow_partial_tiling : bool, default: True
        If false, `size` will be extended so that there are no partial tiles.
        This forces the widget's height and width to be multiples of the tile's
        height and width.
    """
    tile = ResizeProperty()
    allow_partial_tiling = ResizeProperty()

    def __init__(self, *args, tile: Image, allow_partial_tiling=True, is_transparent=True, **kwargs):
        super().__init__(*args, is_transparent=is_transparent, **kwargs)

        self._tile = tile
        self._allow_partial_tiling = allow_partial_tiling

        self.resize(self.size)

    def resize(self, size):
        """
        Resize widget.
        """
        min_height, min_width = size
        tile = self.tile

        vertical_repeat = ceil(min_height / tile.height)
        horizontal_repeat = ceil(min_width / tile.width)

        self._size = vertical_repeat * tile.height, horizontal_repeat * tile.width

        self.canvas = np.tile(tile.canvas, (vertical_repeat, horizontal_repeat))
        self.colors = np.tile(tile.colors, (vertical_repeat, horizontal_repeat, 1))
        self.alpha_channels = np.tile(tile.alpha_channels, (vertical_repeat, horizontal_repeat, 1, 1))

        if self.allow_partial_tiling:
            self._size = size

            vertical_remainder = min_height % tile.height
            horizontal_remainder = min_width % tile.width

            vertical_slice = slice(None, (-tile.height + vertical_remainder) if vertical_remainder else None)
            horizontal_slice = slice(None, (-tile.width + horizontal_remainder) if horizontal_remainder else None)

            self.canvas = self.canvas[vertical_slice, horizontal_slice].copy()
            self.colors = self.colors[vertical_slice, horizontal_slice].copy()
            self.alpha_channels = self.alpha_channels[vertical_slice, horizontal_slice].copy()

        for child in self.children:
            child.update_geometry()

    render = Image.render
