from random import choice

import numpy as np

from nurses_2.widgets.widget_data_structures import Size

from .tetrominoes import TETROMINOS, ARIKA_TETROMINOS


class GridManager:
    def __init__(self, size: Size=Size(23, 10), arika=True)
        self.grid = np.zeros(size, dtype=np.uint8)

        self.tetrominoes = ARIKA_TETROMINOS if arika else TETROMINOS
        for i, tetromino in enumerate(self.tetrominoes):
            tetromino.ENUM = i

        self.held_piece = None
        self.new_piece()

    @property
    def width(self):
        return self.grid.shape[1]

    def new_piece(self, from_held=False):
        if from_held:
            tetromino = self.held_piece
            self.held_piece = None
        else:
            tetromino = self.next_piece
            self.next_piece = choice(self.tetrominoes)

        row_center = self.width >> 1 - tetromino.WIDTH >> 1

        self.current_piece = tetromino(pos=Point(0, row_center), grid=self.grid)
