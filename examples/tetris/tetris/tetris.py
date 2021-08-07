import asyncio
from random import shuffle

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.widget_utilities import clamp

from .color_scheme import *
from .piece import CurrentPiece, GhostPiece, CenteredPiece
from .tetrominoes import TETROMINOS, ARIKA_TETROMINOS

GRAVITY = 1
MAX_LEVEL = 20
FLASH_DELAY = .1
LOCK_DOWN_DELAY = .5
MOVE_RESET = 15

def tetromino_generator(tetrominos):
    """
    Yield each tetromino from a sequence of tetrominos in random order and repeat.
    """
    while True:
        bag = list(tetrominos)
        shuffle(bag)

        while bag:
            yield bag.pop()


class Tetris(Widget):
    def __init__(self, matrix_dim=(22, 10), arika=True, is_transparent=False):
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

        super().__init__(dim=(h, 2 * w + 32), default_color_pair=TETRIS_APP_BACKGROUND_COLOR, is_transparent=is_transparent)

        # TODO: REMOVE HARDCODED POSITIONS AND DIMENSIONS OF DISPLAYS
        # Setup HELD display
        #######################################################################################
        held_border = Widget(dim=(6, 12), pos=(2, 2), default_color_pair=HELD_BORDER_COLOR)   #
        held_border.add_text(f"{'HOLD':^12}")                                                 #
        held_space = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=HELD_BACKGROUND_COLOR) #
        self.held_piece = CenteredPiece()                                                     #
                                                                                              #
        held_border.add_widget(held_space)                                                    #
        held_space.add_widget(self.held_piece)                                                #
        #######################################################################################

        # Setup NEXT display
        ##############################################################################################
        next_border = Widget(dim=(6, 12), pos=(2, 18 + 2 * w), default_color_pair=NEXT_BORDER_COLOR) #
        next_border.add_text(f"{'NEXT':^12}")                                                        #
        next_space = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=NEXT_BACKGROUND_COLOR)        #
        self.next_piece = CenteredPiece()                                                            #
                                                                                                     #
        next_border.add_widget(next_space)                                                           #
        next_space.add_widget(self.next_piece)                                                       #
        ##############################################################################################

        # Setup SCORE display
        ###########################################################################################
        score_border = Widget(dim=(6, 12), pos=(h - 8, 2), default_color_pair=SCORE_BORDER_COLOR) #
        score_border.add_text(f"{'SCORE':^12}")                                                   #
        self.score_display = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=SCORE_COLOR)       #
        score_border.add_widget(self.score_display)                                               #
        ###########################################################################################

        # Setup LEVEL Display
        ####################################################################################################
        level_border = Widget(dim=(6, 12), pos=(h - 8, 18 + 2 * w), default_color_pair=LEVEL_BORDER_COLOR) #
        level_border.add_text(f"{'LEVEL':^12}")                                                            #
        self.level_display = Widget(dim=(4, 8), pos=(1, 2), default_color_pair=LEVEL_COLOR)                #
        level_border.add_widget(self.level_display)                                                        #
        ####################################################################################################

        # `matrix` is a boolean array where True values indicate that a mino exists in that location.
        # `matrix_widget` is a visual representation of `matrix` that carries canvas and color information.
        # These need to be kept in sync with each other.  Anytime one is modified so must the other.
        # (Updates happen in `affix_piece` and `clear_lines` methods.)
        self.matrix = np.zeros(matrix_dim, dtype=np.bool8)
        self.matrix_widget = Widget(dim=(h, 2 * w), pos=(0, 16), default_color_pair=MATRIX_BACKGROUND_COLOR, is_transparent=is_transparent)

        self.ghost_piece = GhostPiece()
        self.current_piece = CurrentPiece()
        self.matrix_widget.add_widgets(self.ghost_piece, self.current_piece)

        self.tetromino_generator = tetromino_generator(ARIKA_TETROMINOS if arika else TETROMINOS)

        self.add_widgets(held_border, next_border, self.matrix_widget, score_border, level_border)

        self._game_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

        self.is_paused = False

    def new_game(self):
        self._game_task.cancel()

        self.matrix[:] = 0
        self.matrix_widget.colors[:, :] = MATRIX_BACKGROUND_COLOR

        self.current_piece.is_enabled = False
        self.next_piece.is_enabled = False
        self.held_piece.is_enabled = False

        self.next_piece.tetromino = next(self.tetromino_generator)

        self._lock_down_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._game_task = asyncio.create_task(self._run_game())

        self.gravity = GRAVITY
        self.lock_down_delay = LOCK_DOWN_DELAY
        self.score = 0
        self.level = 1
        self.lines_to_next_level = 5

        self.new_piece()

    @property
    def score(self):
        return self._score

    @score.setter
    def score(self, value):
        self._score = value
        self.score_display.add_text(f"{value:^8}", row=1)

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self.level_display.add_text(f"{value:^8}", row=0)

    @property
    def lines_to_next_level(self):
        return self._lines_to_next_level

    @lines_to_next_level.setter
    def lines_to_next_level(self, value):
        self._lines_to_next_level = value
        self.level_display.add_text(" Lines: ", row=2)
        self.level_display.add_text(f"{value:^8}", row=3)

    async def _run_game(self):
        while True:
            self.move_current_piece(dy=1, dx=0)
            await asyncio.sleep(self.gravity)

    def pause(self):
        # TODO: Countdown on un-pause
        if self.is_paused:
            self._game_task = asyncio.create_task(self._run_game())
        else:
            self._game_task.cancel()
            self._lock_down_task.cancel()

        self.is_paused = not self.is_paused

    def start_lock_down(self):
        """
        When a piece lands on the stack a lock down timer is started. If not canceled
        the piece will be affixed to the stack after LOCK_DOWN_DELAY seconds.
        """
        self._lock_down_task.cancel()
        self._lock_down_task = asyncio.create_task(self._lock_down_timer())

    async def _lock_down_timer(self):
        try:
            await asyncio.sleep(LOCK_DOWN_DELAY)
        except asyncio.CancelledError:
            return
        else:
            self.affix_piece()

    def update_ghost_position(self):
        ghost = self.ghost_piece

        ghost.pos = self.current_piece.pos
        ghost.orientation = self.current_piece.orientation

        while not self.collides((1, 0), ghost.orientation, ghost):
            self.ghost_piece.top += 1

    def new_piece(self, from_held=False):
        if from_held and not self.can_hold:
            return

        self.can_hold = not from_held

        held_piece = self.held_piece
        next_piece = self.next_piece
        current_piece = self.current_piece

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

        self.ghost_piece.tetromino = current_piece.tetromino
        self.update_ghost_position()

        self.move_reset = 0

        if self.collides((0, 0), self.current_piece.orientation, self.current_piece):
            self._game_task.cancel()
            # TODO: GAMEOVER SCREEN

    def collides(self, offset, orientation, piece):
        """
        Return True if piece collides with stack or boundaries of matrix
        with given offset (from it's current position) and orientation.
        """
        mino_positions = (
            piece.tetromino.mino_positions[orientation]
            + (piece.top, piece.left // 2)
            + offset
        )
        matrix = self.matrix

        return (
            (mino_positions < 0).any()
            or (matrix.shape <= mino_positions).any()
            or matrix[mino_positions[:, 0], mino_positions[:, 1]].any()
        )

    def rotate_current_piece(self, clockwise=True):
        if not self._lock_down_task.done() and self.move_reset >= MOVE_RESET:
            return

        current_piece = self.current_piece
        orientation = current_piece.orientation

        target_orientation = orientation.rotate(clockwise=clockwise)

        for dy, dx in current_piece.tetromino.WALL_KICKS[orientation, target_orientation]:
            if not self.collides((dy, dx), target_orientation, current_piece):
                current_piece.orientation = target_orientation
                current_piece.top += dy
                current_piece.left += 2 * dx

                self.update_ghost_position()

                if self.collides((1, 0), current_piece.orientation, current_piece):
                    if not self._lock_down_task.done():
                        self.move_reset += 1

                    self.start_lock_down()

                else:
                    self._lock_down_task.cancel()

                break

    def move_current_piece(self, dy=0, dx=0):
        current_piece =self.current_piece

        if not self.collides((dy, dx), current_piece.orientation, current_piece):
            if dy == 1:
                current_piece.top += 1

            else:
                if self._lock_down_task.done():
                    pass
                elif self.move_reset < MOVE_RESET:
                    self._lock_down_task.cancel()
                    self.move_reset += 1
                else:
                    return False

                current_piece.left += 2 * dx
                self.update_ghost_position()

            if self.collides((1, 0), current_piece.orientation, current_piece):
                self.start_lock_down()

            return True

        return False

    def affix_piece(self):
        """
        Affix current piece to the stack.
        """
        self._lock_down_task.cancel()

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

                x *= 2
                self.matrix_widget.canvas[y, x: x + 2] = "█"
                self.matrix_widget.colors[y, x: x + 2, :3] = current_piece.tetromino.COLOR

        asyncio.create_task(self.clear_lines())

        self.new_piece()

    async def clear_lines(self):
        """
        Clear completed lines.
        """
        matrix = self.matrix
        completed_lines = np.all(matrix, axis=1)

        if not completed_lines.any():
            return

        not_completed_lines = np.any(~matrix, axis=1)
        matrix_canvas = self.matrix_widget.canvas
        matrix_colors = self.matrix_widget.colors
        old_colors = matrix_colors[completed_lines].copy()

        delay = FLASH_DELAY
        for _ in range(10):
            matrix_colors[completed_lines] = CLEAR_LINE_FLASH_COLOR
            await asyncio.sleep(delay)

            delay *= .8
            matrix_colors[completed_lines] = old_colors
            await asyncio.sleep(delay)

        nlines = completed_lines.sum()

        matrix[nlines:] = matrix[not_completed_lines]
        matrix[:nlines] = 0

        matrix_canvas[nlines:] = matrix_canvas[not_completed_lines]
        matrix_canvas[:nlines] = " "
        matrix_colors[nlines:] = matrix_colors[not_completed_lines]
        matrix_colors[:nlines] = MATRIX_BACKGROUND_COLOR

        self.update_ghost_position()
        self.update_score(nlines)
        self._lock_down_task.cancel()

    def update_score(self, nlines):
        # Original Nintendo Scoring System
        # See https://tetris.wiki/Scoring
        self.score += self.level * (40, 100, 300, 1200)[nlines - 1]

        lines = (1, 3, 5, 8)[nlines - 1]
        if lines >= self.lines_to_next_level:
            self.level += 1
            self.lines_to_next_level = 5 * self.level

            # TODO: Find correct gravity increase
            percent = .95**self.level
            self.gravity = max(.05, percent * GRAVITY)
            self.lock_down_delay = max(.05, percent * LOCK_DOWN_DELAY)
        else:
            self.lines_to_next_level -= lines

    def drop_current_piece(self):
        """
        Drop piece.
        """
        while self.move_current_piece(dy=1):
            pass

    def on_press(self, key_press):
        key = key_press.key

        if self.is_paused:
            if key == "f1":
                self.pause()
                return True

            return False

        if key == "c-m":  # c-m is "enter"
            self.new_game()
            return

        if self._game_task.done():
            return

        current_piece = self.current_piece

        if func := {
            "right": lambda: self.move_current_piece(dx=1),
            "6": lambda: self.move_current_piece(dx=1),
            "left": lambda: self.move_current_piece(dx=-1),
            "4": lambda: self.move_current_piece(dx=-1),
            "down": lambda: self.affix_piece() if not self.move_current_piece(dy=1) else None,
            "2": lambda: self.affix_piece() if not self.move_current_piece(dy=1) else None,
            " ": self.drop_current_piece,
            "8": self.drop_current_piece,
            "c": lambda: self.new_piece(from_held=True),
            "0": lambda: self.new_piece(from_held=True),
            "z": lambda: self.rotate_current_piece(clockwise=False),
            "1": lambda: self.rotate_current_piece(clockwise=False),
            "5": lambda: self.rotate_current_piece(clockwise=False),
            "9": lambda: self.rotate_current_piece(clockwise=False),
            "x": self.rotate_current_piece,
            "up": self.rotate_current_piece,
            "3": self.rotate_current_piece,
            "7": self.rotate_current_piece,
            "f1": self.pause
        }.get(key, False):
            func()
            return True

        return False
