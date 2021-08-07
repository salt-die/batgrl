import numpy as np

from nurses_2.widgets import Widget

from .tetrominoes import Orientation


class Piece(Widget):
    """
    A widget that renders a tetromino.
    """
    def __init__(self, *args, is_transparent=True, is_enabled=False, **kwargs):
        super().__init__(*args, is_transparent=is_transparent, is_enabled=is_enabled, **kwargs)

    @property
    def tetromino(self):
        return self._tetromino

    @tetromino.setter
    def tetromino(self, new_tetromino):
        self.is_enabled = True
        self._tetromino = new_tetromino
        self.orientation = Orientation.UP
        self.resize(new_tetromino.canvases[Orientation.UP].shape)


class CurrentPiece(Piece):
    def render(self, canvas_view, colors_view, rect):
        tetromino = self.tetromino
        orientation = self.orientation

        self.canvas = tetromino.canvases[orientation]
        self.colors = tetromino.colors[orientation]

        super().render(canvas_view, colors_view, rect)


class GhostPiece(Piece):
    TRANSPARENCY = .33

    def render(self, canvas_view, colors_view, rect):
        tetromino = self.tetromino
        orientation = self.orientation

        t, l, b, r, h, w = rect

        index_rect = slice(t, b), slice(l, r)
        canvas = tetromino.canvases[orientation][index_rect]
        colors = tetromino.colors[orientation][index_rect]

        buffer = np.zeros((h, w, 6), dtype=np.float16)

        # RGBA on rgb == rgb + (RGB - rgb) * A
        np.subtract(colors, colors_view, out=buffer, dtype=np.float16)
        np.multiply(buffer, self.TRANSPARENCY, out=buffer)
        np.add(buffer, colors_view, out=buffer, casting="unsafe")

        visible = canvas != " "

        canvas_view[visible] = canvas[visible]
        colors_view[visible] = buffer[visible]


class CenteredPiece(CurrentPiece):
    """
    A Piece that centers itself inside a 4x8 area when resized.
    """
    def resize(self, dim):
        super().resize(dim)
        self.top = 2 - self.height // 2
        self.left = 4 - self.width // 2
