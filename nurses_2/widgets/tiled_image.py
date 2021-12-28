from math import ceil

import numpy as np

from .graphic_widget import GraphicWidget


class TiledImage(GraphicWidget):
    """
    A tiled image.

    Parameters
    ----------
    tile : Image
        The image widget that will used to tile.
    allow_partial_tiling : bool, default: True
        If false, `size` will be extended so that there are no partial tiles.
        This forces the widget's height and width to be multiples of the tile's
        height and width.

    Notes
    -----
    Updating `tile` or `allow_partial_tiling` immediately reloads the tiled widget.
    """
    def __init__(self, *, tile: GraphicWidget, allow_partial_tiling=True, **kwargs):
        super().__init__(**kwargs)

        self._tile = tile
        self._allow_partial_tiling = allow_partial_tiling

        self.resize(self.size)

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, new_tile):
        self._tile = new_tile
        self.resize(self.size)

    @property
    def allow_partial_tiling(self):
        return self._allow_partial_tiling

    @allow_partial_tiling.setter
    def allow_partial_tiling(self, is_allowed):
        self._allow_partial_tiling = is_allowed
        self.resize(self.size)

    def resize(self, size):
        """
        Resize widget.
        """
        h, w = size
        tile = self.tile

        v_repeat = ceil(h / tile.height)
        h_repeat = ceil(w / tile.width)

        texture = np.tile(tile.texture, (v_repeat, h_repeat, 1))

        if self.allow_partial_tiling:
            self._size = size

            vr = h % tile.height
            hr = w % tile.width

            vertical_slice = slice(None, (-tile.height + vr) if vr else None)
            horizontal_slice = slice(None, (-tile.width + hr) if hr else None)

            self.texture = texture[vertical_slice, horizontal_slice].copy()

        else:
            self._size = v_repeat * tile.height, h_repeat * tile.width
            self.texture = texture

        for child in self.children:
            child.update_geometry()
