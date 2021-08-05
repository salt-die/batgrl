from random import shuffle

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors import AutoPositionBehavior
from nurses_2.widgets.widget_data_structures import Size

from .tetrominoes import TETROMINOS, ARIKA_TETROMINOS, Orientation
from .piece import Piece, CenteredPiece

def tetromino_generator(tetrominos):
    while True:
        bag = list(tetrominos)
        shuffle(bag)

        while bag:
            yield bag.pop()


class GameState(Widget):
    def __init__(self, dim: Size=Size(23, 10), arika=True)
        super().__init__(dim=(dim[0], 2 * dim[1]))

        self.matrix = np.zeros(dim, dtype=np.uint8)
        self.tetromino_generator = tetromino_generator(ARIKA_TETROMINOS if arika else TETROMINOS)

        self.held_piece = CenteredPiece(is_enabled=False)
        self.can_hold = True

        self.current_piece = Piece()
        self.next_piece = CenteredPiece()

    def new_piece(self, from_held=False):
        held_piece = self.held_piece
        current_piece = self.current_piece
        next_piece = self.next_piece

        if from_held:
            current_piece.tetromino, held_piece.tetromino = held_piece.tetromino, current_piece.tetromino
        else:
            current_piece.tetromino = next_piece.tetromino
            next_piece.tetromino = next(self.tetromino_generator)

        current_piece.top = 0
        current_piece.left = self.width // 2 - current_piece.width // 2

    def rotate(self, clockwise=True):
        current_piece = self.current_piece
        tetromino = current_piece.tetromino
        orientation = tetromino.orientation

        target_orientation = orientation.rotate(clockwise=clockwise)

        for dy, dx in tetromino.WALL_KICKS[orientation, target_orientation]:
            if not self.collides((dy, dx), target_orientation):
                current_piece.orientation = target_orientation
                current_piece.top += dy
                current_piece.left += dx
                break

    def collides(self, offset, orientation: Orientation):
        """
        Return True if current_piece collides with stack or boundaries of
        matrix with given offset and orientation.
        """
        current_piece = self.current_piece
        mino_positions = (
            current_piece.tetromino.mino_positions[orientation]
            + current_piece.pos
            + offset
        )
        matrix = self.matrix

        return (
            (mino_positions < 0)
            | (matrix.shape <= mino_positions)
            | matrix[mino_positions[:, 0], mino_positions[:, 1]]
        ).any()
