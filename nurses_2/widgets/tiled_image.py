from math import ceil

import numpy as np

from .graphic_widget import GraphicWidget, Size


class TiledImage(GraphicWidget):
    """
    A tiled image.

    Parameters
    ----------
    tile : GraphicWidget
        The graphic widget that will used to tile.

    Notes
    -----
    Setting `tile` immediately updates the texture.
    """
    def __init__(self, *, tile: GraphicWidget, **kwargs):
        super().__init__(**kwargs)
        self._tile = tile
        self.resize(self.size)

    @property
    def tile(self):
        return self._tile

    @tile.setter
    def tile(self, new_tile):
        self._tile = new_tile
        self.resize(self.size)

    def resize(self, size: Size):
        """
        Resize widget.
        """
        super(GraphicWidget, self).resize(size)

        h, w = self._size
        tile = self.tile

        v_repeat = ceil(h / tile.height)
        h_repeat = ceil(w / tile.width)

        texture = np.tile(tile.texture, (v_repeat, h_repeat, 1))

        vr = h % tile.height
        hr = w % tile.width

        vertical_slice = np.s_[: (-tile.height + vr) if vr else None]
        horizontal_slice = np.s_[: (-tile.width + hr) if hr else None]

        self.texture = texture[vertical_slice, horizontal_slice].copy()
