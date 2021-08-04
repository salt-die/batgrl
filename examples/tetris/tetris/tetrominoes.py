from typing import List

import numpy as np

from nurses_2.widgets.widget_data_structures import Point
from nurses_2.colors import CYAN, YELLOW, GREEN, RED, BLUE, Color

from .orientation import Orientation
from .wall_kicks import *

PURPLE = Color.from_hex("#800080")
ORANGE = Color.from_hex("#FF7F00")


class Tetromino:
    WALL_KICKS: dict
    BASE_SHAPE: List[List[int]]
    COLOR: Color
    HALF_WIDTH: int

    def __init_subclass__(cls):
        base = np.array(cls.BASE_SHAPE, dtype=np.uint8)

        cls.shapes = {
            Orientation.UP:    base,
            Orientation.LEFT:  np.rot90(base, 1),
            Orientation.DOWN:  np.rot90(base, 2),
            Orientation.RIGHT: np.rot90(base, 3),
        }

        cls.mino_positions = {
            orientation: np.argwhere(shape) for orientation, shape in cls.shapes.items()
        }

        cls.HALF_WIDTH = len(cls.BASE_SHAPE) >> 1

    def __init__(self, pos: Point, grid):
        self.pos = np.array(pos)
        self.grid = grid
        self.orientation = Orientation.UP

    @property
    def shape(self):
        return self.shapes[self.orientation]

    def rotate(self, clockwise=True):
        orientation = self.orientation

        target_orientation = (
            orientation.clockwise() if clockwise else orientation.counter_clockwise()
        )

        for offset in self.WALL_KICKS[orientation, target_orientation]:
            if not self.collides(offset, target_orientation):
                self.orientation = target_orientation
                self.pos += offset
                break

    def collides(self, offset: Point, orientation: Orientation):
        """
        Return True if tetromino collides with stack or boundaries with given
        offset and orientation.
        """
        mino_positions = self.mino_positions[orientation] + self.pos + offset
        grid = self.grid

        return (
            (mino_positions < 0)
            | (grid.shape <= mino_positions)
            | grid[mino_positions[:, 0], mino_positions[:, 1]]
        ).any()

    @property
    def can_fall(self):
        return not self.collides((1, 0), self.orientation)


class J(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = BLUE


class L(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = ORANGE


class S(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
    ]
    COLOR = GREEN


class T(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = PURPLE


class Z(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0],
    ]
    COLOR = RED


class I(Tetromino):
    WALL_KICKS = I_WALL_KICKS
    BASE_SHAPE = [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    COLOR = CYAN


class ArikaI(Tetromino):
    WALL_KICKS = ARIKA_I_WALL_KICKS
    BASE_SHAPE = I.BASE_SHAPE
    COLOR = I.COLOR


class O(Tetromino):
    WALL_KICKS = O_WALL_KICKS
    BASE_SHAPE = [
        [1, 1],
        [1, 1],
    ]
    COLOR = YELLOW


TETROMINOS = J, L, S, T, Z, I, O,
ARIKA_TETROMINOS = J, L, S, T, Z, ArikaI, O,
