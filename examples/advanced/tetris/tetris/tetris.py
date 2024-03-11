import asyncio
from collections import deque
from itertools import count
from pathlib import Path
from random import shuffle

import numpy as np
from batgrl.colors import AWHITE
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.image import Image
from batgrl.gadgets.text import Text
from batgrl.gadgets.texture_tools import composite

from .matrix import MatrixGadget
from .modal_screen import ModalScreen
from .tetrominoes import ARIKA_TETROMINOS, TETROMINOS, Orientation

MAX_LEVEL = 20
FLASH_DELAY = 0.1
LOCK_DOWN_DELAY = 0.5
MOVE_RESET = 15
QUEUE_ID = count()
ASSETS = Path(__file__).parent.parent.parent.parent / "assets"
TETRIS_BACKGROUND_PATH = ASSETS / "loudypixelsky.png"


def gravity(level):
    """
    Tetromino fall speed per level.

    See Also
    --------
    https://harddrop.com/wiki/Tetris_Worlds
    """
    return (0.8 - ((level - 1) * 0.007)) ** (level - 1)


def tetromino_generator(tetrominos):
    """Yield each tetromino from a sequence of tetrominos in random order and repeat."""
    bag = list(tetrominos)
    while True:
        shuffle(bag)
        yield from bag


class Piece(Graphics):
    @property
    def tetromino(self):
        return self._tetromino

    @tetromino.setter
    def tetromino(self, new_tetromino):
        self._tetromino = new_tetromino
        self.is_enabled = True
        self.orientation = Orientation.UP

    @property
    def orientation(self):
        return self._orientation

    @orientation.setter
    def orientation(self, orientation):
        self._orientation = orientation
        h, w, _ = self._tetromino.textures[orientation].shape
        self.texture = self._tetromino.textures[self._orientation]
        self.size = h // 2, w
        self.apply_hints()


class Tetris(Image):
    def __init__(self, matrix_size=(22, 10), arika=True, **kwargs):
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
        bsize = bh, bw = (
            4 + 2 * BORDER_WIDTH,
            8 + 4 * BORDER_WIDTH,
        )  # border size; border height, border width
        h, w = matrix_size

        outer_kwargs = {
            "size": bsize,
            "is_transparent": True,
            "alpha": 0.5,
        }
        inner_kwargs = {
            "size": (4, 8),
            "pos": (BORDER_WIDTH, 2 * BORDER_WIDTH),
            "is_transparent": True,
            "alpha": 0.0,
        }

        # offsets for border gadgets
        top = SPACING
        bottom = h - (bh + SPACING)
        left = SPACING
        right = 3 * SPACING + bw + 2 * w

        super().__init__(
            size=(h, 4 * SPACING + 2 * bw + 2 * w),
            path=TETRIS_BACKGROUND_PATH,
            **kwargs,
        )
        self.tetromino_generator = tetromino_generator(
            ARIKA_TETROMINOS if arika else TETROMINOS
        )
        self._level = 0
        self.is_paused = False

        # Setup HELD display
        held_border = Text(pos=(top, left), **outer_kwargs)
        held_border.add_str(f"{'HOLD':^{bsize[1]}}")
        held_space = Text(**inner_kwargs)

        held_border.add_gadget(held_space)

        # Setup NEXT display
        next_border = Text(pos=(top, right), **outer_kwargs)
        next_border.add_str(f"{'NEXT':^{bsize[1]}}")
        next_space = Text(**inner_kwargs)
        next_border.add_gadget(next_space)

        # Setup SCORE display
        score_border = Text(pos=(bottom, left), **outer_kwargs)
        score_border.add_str(f"{'SCORE':^{bsize[1]}}")
        self.score_display = Text(**inner_kwargs)
        score_border.add_gadget(self.score_display)

        # Setup LEVEL Display
        level_border = Text(pos=(bottom, right), **outer_kwargs)
        level_border.add_str(f"{'LEVEL':^{bsize[1]}}")
        self.level_display = Text(**inner_kwargs)

        level_border.add_gadget(self.level_display)

        self.add_gadgets(held_border, next_border, score_border, level_border)

        self.held_piece = Piece(
            pos_hint={"y_hint": 0.5, "x_hint": 0.5}, is_enabled=False
        )
        held_space.add_gadget(self.held_piece)

        self.next_piece = Piece(
            pos_hint={"y_hint": 0.5, "x_hint": 0.5}, is_enabled=False
        )
        next_space.add_gadget(self.next_piece)

        self.matrix = np.zeros(matrix_size, dtype=np.bool8)
        """Bool array representation of mino positions."""
        self.matrix_gadget = MatrixGadget(size=(h, 2 * w), pos=(0, 2 * SPACING + bw))
        """The "matrix", where minos land."""

        self.on_size()

        self.ghost_piece = Piece(alpha=0.33, is_enabled=False)
        self.current_piece = Piece(is_enabled=False)
        self.matrix_gadget.add_gadgets(self.ghost_piece, self.current_piece)

        self.add_gadget(self.matrix_gadget)

        self.modal_screen = ModalScreen()

    def on_add(self):
        super().on_add()
        self.root.add_gadget(self.modal_screen)
        self._game_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._lock_down_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._clear_lines_queue = deque()

    def on_remove(self):
        super().on_remove()
        if self.modal_screen.parent:
            self.modal_screen.parent.remove_gadget(self.modal_screen)
        self._game_task.cancel()
        self._lock_down_task.cancel()
        for task in self._clear_lines_queue:
            task.cancel()

    def on_size(self):
        super().on_size()
        if hasattr(self, "matrix_gadget"):
            # Darken background behind matrix.
            left = self.matrix_gadget.left
            right = self.matrix_gadget.right
            self.texture[:, left:right, :3] //= 3

    def new_game(self):
        self._game_task.cancel()
        self._lock_down_task.cancel()
        while self._clear_lines_queue:
            self._clear_lines_queue.popleft().cancel()

        self.matrix[:] = 0
        self.matrix_gadget.clear()

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
        self.score_display.add_str(f"{value:^8}", pos=(1, 0))

    @property
    def level(self):
        return self._level

    @level.setter
    def level(self, value):
        self._level = value
        self.level_display.add_str(f"{value:^8}")

    @property
    def lines_to_next_level(self):
        return self._lines_to_next_level

    @lines_to_next_level.setter
    def lines_to_next_level(self, value):
        self._lines_to_next_level = value
        self.level_display.add_str(" Lines: ", pos=(2, 0))
        self.level_display.add_str(f"{value:^8}", pos=(3, 0))

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
            modal.add_str(
                f"{f'Current Score: {self.score}':^{modal.width}}", pos=(-2, 0)
            )

        self.is_paused = not self.is_paused

    def start_lock_down(self):
        """
        When a piece lands on the stack a lock down timer is started. If not canceled
        the piece will be affixed to the stack after LOCK_DOWN_DELAY seconds.
        """
        self._lock_down_task.cancel()
        self._lock_down_task = asyncio.create_task(self._lock_down_timer())

    async def _lock_down_timer(self):
        await asyncio.sleep(LOCK_DOWN_DELAY)
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
                current_piece.tetromino, held_piece.tetromino = (
                    held_piece.tetromino,
                    current_piece.tetromino,
                )
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
            modal.add_str(f"{f'Final Score: {self.score}':^{modal.width}}", pos=(-2, 0))

    def collides(self, offset, piece, orientation=None):
        """
        Whether piece collides with stack or boundaries of matrix with given
        offset (from it's current position) and orientation.
        """
        if orientation is None:
            orientation = piece.orientation

        mino_positions = (
            piece.tetromino.mino_positions[orientation]
            + (piece.top, piece.left // 2)
            + offset
        )
        return (
            (mino_positions < 0).any()
            or (self.matrix.shape <= mino_positions).any()
            or self.matrix[mino_positions[:, 0], mino_positions[:, 1]].any()
        )

    def rotate_current_piece(self, clockwise=True):
        if not self._lock_down_task.done() and self.move_reset >= MOVE_RESET:
            return

        current_piece = self.current_piece
        orientation = current_piece.orientation

        target_orientation = orientation.rotate(clockwise=clockwise)

        for dy, dx in current_piece.tetromino.kicks[orientation, target_orientation]:
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
        """Move current piece. Returns true if the move was successful else false."""
        current_piece = self.current_piece

        if not self.collides((dy, dx), current_piece):
            if dy == 1:
                current_piece.top += 1

            else:
                if self._lock_down_task.done():
                    pass
                elif self.move_reset < MOVE_RESET:
                    self._lock_down_task.cancel()
                    self.move_reset += 1
                else:  # Lock down task was started and move reset surpassed.
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
        """Affix current piece to the stack."""
        self._lock_down_task.cancel()

        current_piece = self.current_piece
        y, x = current_piece.pos

        ys, xs = (
            current_piece.tetromino.mino_positions[current_piece.orientation]
            + (y, x // 2)
        ).T
        self.matrix[ys, xs] = 1

        composite(
            current_piece.texture,
            self.matrix_gadget.texture,
            (2 * y, x),
        )
        task_name = str(next(QUEUE_ID))
        self._clear_lines_queue.append(
            asyncio.create_task(self.clear_lines(task_name), name=task_name)
        )

        self.new_piece()

    async def clear_lines(self, task_name):
        """Clear completed lines."""
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

        matrix_texture = self.matrix_gadget.texture
        matrix_lines = np.kron(completed_lines, [True, True])
        old_texture = matrix_texture[matrix_lines].copy()

        delay = FLASH_DELAY * 0.95 ** (self.level - 1)
        for _ in range(10):
            matrix_texture[matrix_lines] = AWHITE
            await asyncio.sleep(delay)

            delay *= 0.8
            matrix_texture[matrix_lines] = old_texture
            await asyncio.sleep(delay)

        nlines = completed_lines.sum()

        matrix[nlines:] = matrix[~completed_lines]
        matrix[:nlines] = 0

        matrix_texture[2 * nlines :] = matrix_texture[~matrix_lines]
        matrix_texture[: 2 * nlines] = 0

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
            self.gravity = max(0.05, gravity(self.level))
            self.lock_down_delay = max(0.05, 0.95 ** (self.level - 1) * LOCK_DOWN_DELAY)
        else:
            self.lines_to_next_level -= lines

    def drop_current_piece(self):
        """Drop piece."""
        while self.move_current_piece(dy=1):
            pass

    def on_key(self, key_event):
        match key_event.key:
            case "f1":
                self.pause()
            case "enter":
                self.new_game()
            case "right" | "6":
                self.move_current_piece(dx=1)
            case "left" | "4":
                self.move_current_piece(dx=-1)
            case "down" | "2":
                if not self.move_current_piece(dy=1):
                    self.affix_piece()
            case " " | "8":
                self.drop_current_piece()
            case "c" | "0":
                self.new_piece(from_held=True)
            case "z" | "1" | "5" | "9":
                self.rotate_current_piece(clockwise=False)
            case "x" | "up" | "3" | "7":
                self.rotate_current_piece()
            case _:
                return False

        return True
