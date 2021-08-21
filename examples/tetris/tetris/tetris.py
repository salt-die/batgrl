import asyncio
from collections import deque
from itertools import count
from pathlib import Path
from random import shuffle

import numpy as np

from nurses_2.widgets import Widget
from nurses_2.widgets.image import Image

from .color_scheme import CLEAR_LINE_FLASH_COLOR
from .matrix import MatrixWidget
from .modal_screen import ModalScreen
from .piece import CurrentPiece, GhostPiece, CenteredPiece
from .tetrominoes import TETROMINOS, ARIKA_TETROMINOS

MAX_LEVEL = 20
FLASH_DELAY = .1
LOCK_DOWN_DELAY = .5
MOVE_RESET = 15
QUEUE_ID = count()
TETRIS_BACKGROUND_PATH = Path("..") / "images" / "background_2.png"

def gravity(level):
    """
    Tetromino fall speed per level.

    See Also
    --------
    https://harddrop.com/wiki/Tetris_Worlds
    """
    return (0.8 - ((level - 1) * 0.007))**(level - 1)

def tetromino_generator(tetrominos):
    """
    Yield each tetromino from a sequence of tetrominos in random order and repeat.
    """
    while True:
        bag = list(tetrominos)
        shuffle(bag)

        while bag:
            yield bag.pop()

def setup_background(widget):
    t, l, b, r, _, _ = widget.rect
    widget.colors[..., 3:] = widget.parent.colors[t: b, l: r, 3:] // 2


class Tetris(Image):
    def __init__(self, matrix_size=(22, 10), arika=True):
        ##################################################################
        # Tetris Layout includes the matrix (where pieces stack) and two #
        # displays for held piece and next piece. Piece displays have    #
        # width 8, spacing has width S, and borders have width B.        #
        #                                                                #
        #                      Total width:                              #
        #  S + B + 8 + B + S +    2 * w    + S + B + 8 + B + S           #
        #                      +---------+                               #
        #      +-------+       |         |       +-------+               #
        #      | held  |       | matrix  |       | next  |               #
        #      +-------+       |         |       +-------+               #
        #                      |         |                               #
        ##################################################################
        SPACING = 3
        BORDER_WIDTH = 1

        display_geometry = {
            'size': (4, 8),
            'pos': (BORDER_WIDTH, 2 * BORDER_WIDTH),
        }

        bsize = bh, bw = 4 + 2 * BORDER_WIDTH, 8 + 4 * BORDER_WIDTH  # border size; border height, border width
        h, w = matrix_size

        t, b, l, r = SPACING, h - (bh + SPACING), SPACING, 3 * SPACING + bw + 2 * w  # offsets for border widgets

        super().__init__(
            size=(h, 4 * SPACING + 2 * bw + 2 * w),
            path=TETRIS_BACKGROUND_PATH,
        )
        self.tetromino_generator = tetromino_generator(ARIKA_TETROMINOS if arika else TETROMINOS)
        self._level = 0
        self._game_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._lock_down_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._clear_lines_queue = deque()

        self.is_paused = False

        # Setup HELD display
        ##############################################
        held_border = Widget(size=bsize, pos=(t, l))   #
        held_border.add_text(f"{'HOLD':^{bsize[1]}}") #
        held_space = Widget(**display_geometry)      #
                                                     #
        held_border.add_widget(held_space)           #
        ##############################################

        # Setup NEXT display
        ##############################################
        next_border = Widget(size=bsize, pos=(t, r))   #
        next_border.add_text(f"{'NEXT':^{bsize[1]}}") #
        next_space = Widget(**display_geometry)      #
                                                     #
        next_border.add_widget(next_space)           #
        ##############################################

        # Setup SCORE display
        #################################################
        score_border = Widget(size=bsize, pos=(b, l))     #
        score_border.add_text(f"{'SCORE':^{bsize[1]}}")  #
        self.score_display = Widget(**display_geometry) #
                                                        #
        score_border.add_widget(self.score_display)     #
        #################################################

        # Setup LEVEL Display
        #################################################
        level_border = Widget(size=bsize, pos=(b, r))     #
        level_border.add_text(f"{'LEVEL':^{bsize[1]}}")  #
        self.level_display = Widget(**display_geometry) #
                                                        #
        level_border.add_widget(self.level_display)     #
        #################################################

        self.add_widgets(held_border, next_border, score_border, level_border)

        for widget in self.walk():
            setup_background(widget)

        self.held_piece = CenteredPiece()
        held_space.add_widget(self.held_piece)

        self.next_piece = CenteredPiece()
        next_space.add_widget(self.next_piece)

        # matrix is a boolean array where True values indicate that a mino exists in that location.
        self.matrix = np.zeros(matrix_size, dtype=np.bool8)
        # matrix_widget is the visual representation of matrix
        self.matrix_widget = MatrixWidget(
            size=(h, 2 * w),
            pos=(0, 2 * SPACING + bw),
            is_transparent=True,
        )

        self.ghost_piece = GhostPiece()
        self.current_piece = CurrentPiece()
        self.matrix_widget.add_widgets(self.ghost_piece, self.current_piece)

        self.add_widget(self.matrix_widget)

        # Darken background behind matrix.
        left = self.matrix_widget.left
        right = self.matrix_widget.right
        self.colors[:, left:right] //= 3

        self.modal_screen = ModalScreen()
        self.add_widget(self.modal_screen)

    def new_game(self):
        self._game_task.cancel()
        self._lock_down_task.cancel()
        while self._clear_lines_queue:
            self._clear_lines_queue.popleft().cancel()

        self.matrix[:] = 0
        self.matrix_widget.canvas[:] = " "

        self.current_piece.is_enabled = False
        self.next_piece.is_enabled = False
        self.held_piece.is_enabled = False

        self.next_piece.tetromino = next(self.tetromino_generator)

        self._game_task = asyncio.create_task(self._run_game())

        self.level = 1
        self.score = 0
        self.gravity = gravity(self.level)
        self.lock_down_delay = LOCK_DOWN_DELAY
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
        if self.is_paused:
            self._game_task = asyncio.create_task(self._run_game())
        else:
            self._game_task.cancel()
            self._lock_down_task.cancel()

            modal = self.modal_screen
            modal.enable(callback=self.pause, is_game_over=False)
            modal.add_text(f"{f'Current Score: {self.score}':^{modal.width}}", row=-2)

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

        while not self.collides((1, 0), ghost):
            self.ghost_piece.top += 1

    def new_piece(self, from_held=False):
        if from_held and not self.can_hold:
            return

        self._lock_down_task.cancel()
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
        current_piece.left = (self.matrix.shape[1] // 2 - current_piece.width // 4) * 2

        self.ghost_piece.tetromino = current_piece.tetromino
        self.update_ghost_position()

        self.move_reset = 0

        if self.collides((0, 0), current_piece):
            self._game_task.cancel()
            modal = self.modal_screen
            modal.enable(callback=self.new_game, is_game_over=True)
            modal.add_text(f"{f'Final Score: {self.score}':^{modal.width}}", row=-2)

    def collides(self, offset, piece, orientation=None):
        """
        Return True if piece collides with stack or boundaries of matrix
        with given offset (from it's current position) and orientation.
        """
        if orientation is None:
            orientation = piece.orientation

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
            if not self.collides((dy, dx), current_piece, target_orientation):
                current_piece.orientation = target_orientation
                current_piece.top += dy
                current_piece.left += 2 * dx

                self.update_ghost_position()

                if self.collides((1, 0), current_piece):
                    if not self._lock_down_task.done():
                        self.move_reset += 1

                    self.start_lock_down()

                else:
                    self._lock_down_task.cancel()

                break

    def move_current_piece(self, dy=0, dx=0):
        current_piece =self.current_piece

        if not self.collides((dy, dx), current_piece):
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

            if self.collides((1, 0), current_piece):
                self.start_lock_down()

            return True

        elif dy and self._lock_down_task.done():
            self.start_lock_down()

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

        for y, x in mino_positions:
            if 0 <= y < h and 0 <= x < w:
                self.matrix[y, x] = 1

                x *= 2
                self.matrix_widget.canvas[y, x: x + 2] = "█"
                self.matrix_widget.colors[y, x: x + 2, :3] = current_piece.tetromino.COLOR

        task_name = str(next(QUEUE_ID))
        self._clear_lines_queue.append(
            asyncio.create_task(self.clear_lines(task_name), name=task_name)
        )

        self.new_piece()

    async def clear_lines(self, task_name):
        """
        Clear completed lines.
        """
        # To prevent multiple line clears from interfering with each
        # other they are run sequentially:
        queue = self._clear_lines_queue

        while queue[0].get_name() != task_name:
            if queue[0].done():
                queue.popleft()
            else:
                await queue[0]

        matrix = self.matrix
        completed_lines = np.all(matrix, axis=1)

        if not completed_lines.any():
            return

        not_completed_lines = np.any(~matrix, axis=1)
        matrix_canvas = self.matrix_widget.canvas
        matrix_colors = self.matrix_widget.colors
        old_colors = matrix_colors[completed_lines].copy()

        delay = FLASH_DELAY * .95**(self.level - 1)
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
            self.gravity = max(.05, gravity(self.level))
            self.lock_down_delay = max(.05, .95**(self.level - 1) * LOCK_DOWN_DELAY)
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

        # Named lambdas.  Do something about it.
        move_right = lambda: self.move_current_piece(dx=1)
        move_left = lambda: self.move_current_piece(dx=-1)
        move_down = lambda: self.affix_piece() if not self.move_current_piece(dy=1) else None
        use_held = lambda: self.new_piece(from_held=True)
        rotate_ccw = lambda: self.rotate_current_piece(clockwise=False)

        if handle := {
            "f1"   : self.pause,
            "c-m"  : self.new_game,
            "right": move_right,
            "6"    : move_right,
            "left" : move_left,
            "4"    : move_left,
            "down" : move_down,
            "2"    : move_down,
            " "    : self.drop_current_piece,
            "8"    : self.drop_current_piece,
            "c"    : use_held,
            "0"    : use_held,
            "z"    : rotate_ccw,
            "1"    : rotate_ccw,
            "5"    : rotate_ccw,
            "9"    : rotate_ccw,
            "x"    : self.rotate_current_piece,
            "up"   : self.rotate_current_piece,
            "3"    : self.rotate_current_piece,
            "7"    : self.rotate_current_piece,
            "f1"   : self.pause,
        }.get(key, False):
            handle()
            return True

        return False
