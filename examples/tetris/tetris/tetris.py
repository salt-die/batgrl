import asyncio
from random import shuffle

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.widget_utilities import clamp

from .color_scheme import *
from .piece import Piece, CenteredPiece
from .tetrominoes import TETROMINOS, ARIKA_TETROMINOS

FLASH_DELAY = .1

def tetromino_generator(tetrominos):
    """
    Yield each tetromino from a sequence of tetrominos in random order and repeat.
    """
    while True:
        bag = list(tetrominos)
        shuffle(bag)

        while bag:
            yield bag.pop()

# TODO: Add ghost piece
class Tetris(Widget):
    def __init__(self, matrix_dim=(23, 10), arika=True):
        ##################################################################
        # Tetris Layout includes the matrix (where pieces stack) and two #
        # displays for held piece and next piece. Piece displays are 4x8 #
        # with 1x2 borders. Empty space between display components has   #
        # width 2.                                                       #
        #                                                                #
        #                      Total width:                              #
        #                                                                #
        #  2 + 2 + 8 + 2 + 2 +    2 * w    + 2 + 2 + 8 + 2 + 2           #
        #      +-------+       +---------+       +-------+               #
        #      | held  |       |         |       | next  |               #
        #      +-------+       | matrix  |       +-------+               #
        #                      |         |                               #
        ##################################################################

        h, w = matrix_dim

        super().__init__(dim=(h, 2 * w + 32), default_color_pair=TETRIS_APP_BACKGROUND_COLOR)

        # Setup held display
        #######################################################################################
        held_border = Widget(dim=(6, 12), pos=(2, 2), default_color_pair=HELD_BORDER_COLOR)   #
        held_space = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=HELD_BACKGROUND_COLOR) #
        self.held_piece = CenteredPiece()                                                     #
                                                                                              #
        held_border.add_widget(held_space)                                                    #
        held_space.add_widget(self.held_piece)                                                #
        #######################################################################################

        # Setup next display
        ##############################################################################################
        next_border = Widget(dim=(6, 12), pos=(2, 18 + 2 * w), default_color_pair=NEXT_BORDER_COLOR) #
        next_space = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=NEXT_BACKGROUND_COLOR)        #
        self.next_piece = CenteredPiece()                                                            #
                                                                                                     #
        next_border.add_widget(next_space)                                                           #
        next_space.add_widget(self.next_piece)                                                       #
        ##############################################################################################

        # `matrix` is just a boolean array where True values indicate that a mino exists in that location.
        # `matrix_widget` is a visual representation of `matrix` that carries color information as well.
        # These need to be kept in sync with each other.  Anytime one is modified so must the other.
        self.matrix = np.zeros(matrix_dim, dtype=np.bool8)
        self.matrix_widget = Widget(dim=(h, 2 * w), pos=(0, 16), default_color_pair=MATRIX_BACKGROUND_COLOR)
        self.current_piece = Piece()

        self.matrix_widget.add_widget(self.current_piece)

        self.tetromino_generator = tetromino_generator(ARIKA_TETROMINOS if arika else TETROMINOS)

        self.add_widgets(held_border, next_border, self.matrix_widget)

        self._game_task = asyncio.create_task(asyncio.sleep(0))  # dummy task


    def new_game(self):
        self._game_task.cancel()

        self.matrix[:] = 0
        self.matrix_widget.colors[:, :] = MATRIX_BACKGROUND_COLOR

        self.current_piece.is_enabled = False
        self.next_piece.is_enabled = False
        self.held_piece.is_enabled = False

        self.next_piece.tetromino = next(self.tetromino_generator)
        self.can_hold = True
        self.new_piece()

        self.delay = 1
        self._game_task = asyncio.create_task(self._run_game())

    async def _run_game(self):
        while True:
            if self.current_piece_can_fall:
                self.current_piece.top += 1
            else:
                # TODO: add delay before affix
                self.affix_piece()

            await asyncio.sleep(self.delay)

    def new_piece(self, from_held=False):
        held_piece = self.held_piece
        current_piece = self.current_piece
        next_piece = self.next_piece

        if from_held:
            if held_piece.is_enabled:
                current_piece.tetromino, held_piece.tetromino = held_piece.tetromino, current_piece.tetromino
            else:
                held_piece.tetromino = current_piece.tetromino
                current_piece.tetromino = next_piece.tetromino
                next_piece.tetromino = next(self.tetromino_generator)
        else:
            current_piece.tetromino = next_piece.tetromino
            next_piece.tetromino = next(self.tetromino_generator)

        current_piece.top = 0
        current_piece.left = (self.matrix.shape[1] // 2 - current_piece.width // 2) * 2

    def hold(self):
        if self.can_hold:
            self.new_piece(from_held=True)
            self.can_hold = False

    def rotate(self, clockwise=True):
        current_piece = self.current_piece
        orientation = current_piece.orientation

        target_orientation = orientation.rotate(clockwise=clockwise)

        for dy, dx in current_piece.tetromino.WALL_KICKS[orientation, target_orientation]:
            if not self.collides((dy, dx), target_orientation):
                current_piece.orientation = target_orientation
                current_piece.top += dy
                current_piece.left += 2 * dx
                break

    def collides(self, offset, orientation):
        """
        Return True if current_piece collides with stack or boundaries of
        matrix with given offset (from it's current position) and orientation.
        """
        current_piece = self.current_piece
        mino_positions = (
            current_piece.tetromino.mino_positions[orientation]
            + (current_piece.top, current_piece.left // 2)
            + offset
        )
        matrix = self.matrix

        return (
            (mino_positions < 0).any()
            or (matrix.shape <= mino_positions).any()
            or matrix[mino_positions[:, 0], mino_positions[:, 1]].any()
        )

    @property
    def current_piece_can_fall(self):
        return not self.collides((1, 0), self.current_piece.orientation)

    def affix_piece(self):
        """
        Affix current piece to the stack. If holding was not allowed, it will be after an affix.
        """
        current_piece = self.current_piece
        mino_positions = (
            current_piece.tetromino.mino_positions[current_piece.orientation]
            + (current_piece.top, current_piece.left // 2)
        )

        h, w = self.matrix.shape

        # TODO: vectorize
        for y, x in mino_positions:
            if 0 <= y < h and 0 <= x < w:
                self.matrix[y, x] = 1
                self.matrix_widget.colors[y, 2 * x, 3:] = current_piece.tetromino.COLOR
                self.matrix_widget.colors[y, 2 * x + 1, 3:] = current_piece.tetromino.COLOR

        asyncio.create_task(self.clear_lines())

        self.can_hold = True

        self.new_piece()

        if self.collides((0, 0), self.current_piece.orientation):
            self._game_task.cancel()

            # TODO: GAMEOVER SCREEN

    async def clear_lines(self):
        """
        Clear completed lines.
        """
        matrix = self.matrix
        matrix_colors = self.matrix_widget.colors

        completed_lines = np.all(matrix, axis=1)

        if not completed_lines.any():
            return

        old_colors = matrix_colors[completed_lines].copy()

        delay = FLASH_DELAY
        for _ in range(10):
            matrix_colors[completed_lines] = CLEAR_LINE_FLASH_COLOR
            await asyncio.sleep(delay)

            delay *= .8
            matrix_colors[completed_lines] = old_colors
            await asyncio.sleep(delay)

        not_completed_lines = np.any(~matrix, axis=1)

        empty = completed_lines.sum()

        matrix[empty:] = matrix[not_completed_lines]
        matrix[:empty] = 0

        matrix_colors[empty:] = matrix_colors[not_completed_lines]
        matrix_colors[:empty] = MATRIX_BACKGROUND_COLOR

    def drop(self):
        """
        Drop piece and affix.
        """
        while self.current_piece_can_fall:
            self.current_piece.top += 1

        self.affix_piece()

    def on_press(self, key_press):
        if key_press.key == 'c-m':
            self.new_game()
            return

        if self._game_task.done():
            return

        current_piece = self.current_piece

        if key_press.key == 'd':
            if not self.collides((0, 1), current_piece.orientation):
                current_piece.left += 2
        elif key_press.key == 'a':
            if not self.collides((0, -1), current_piece.orientation):
                current_piece.left -= 2
        elif key_press.key == 's':
            if self.current_piece_can_fall:
                current_piece.top += 1
            else:
                self.affix_piece()
        elif key_press.key == ' ':
            self.drop()
        elif key_press.key == 'q':
            self.rotate(clockwise=False)
        elif key_press.key == 'e':
            self.rotate(clockwise=True)
        elif key_press.key == 'r':
            self.hold()
        else:
            return False

        return True
