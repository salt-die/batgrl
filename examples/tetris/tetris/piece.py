from nurses_2.widgets import Widget

from .tetrominoes import Orientation


class Piece(Widget):
    """
    A widget that renders a tetromino.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, is_transparent=True, **kwargs)
        self.tetromino = self

    @property
    def tetromino(self):
        return self._tetromino

    @tetromino.setter
    def tetromino(self, new_tetromino)
        self._tetromino = new_tetromino
        self.orientation = Orientation.UP
        self.resize(new_tetromino.canvases[Orientation.UP].shape)

    def render(self, canvas_view, colors_view, rect):
        tetromino = self.tetromino
        orientation = self.orientation

        self.canvas = tetromino.canvases[orientation]
        self.colors = tetromino.colors[orientation]

        super().render(canvas_view, colors_view, rect)


class CenteredPiece(Piece):
    """
    A Piece that centers itself inside a 4x4 area when resized.
    """
    def resize(self, dim):
        super().resize(dim)
        self.top = 2 - self.height // 2
        self.left = 2 - self.width // 2
