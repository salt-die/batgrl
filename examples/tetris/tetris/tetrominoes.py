from enum import IntFlag

import numpy as np

from nurses_2.colors import CYAN, YELLOW, GREEN, RED, BLUE, Color

from .wall_kicks import *

PURPLE = Color.from_hex("#800080")
ORANGE = Color.from_hex("#FF7F00")


class Orientation(IntFlag):
    """
    Orientation of a tetromino.
    """
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    def clockwise(self):
        return Orientation((self + 1) % 4)

    def counter_clockwise(self):
        return Orientation((self - 1) % 4)


class Tetromino:
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

        cls.canvases = {
            orientation: self._to_nurses_canvas(shape) for orientation, shape in cls.shapes.items()
        }

        cls.colors = {
            orientation: self._to_nurses_colors(shape) for orientation, shape in cls.shapes.colors()
        }

    @staticmethod
    def _to_nurses_canvas(shape):
        """
        Return a nurses canvas from a shape array.
        """
        return np.repeat(np.where(shape, "█", " "), 2, axis=1,)

    @classmethod
    def _to_nurses_colors(cls, shape):
        """
        Return a nurses color array from a shape array.
        """
        colors = np.zeros((*shape.shape, 3), dtype=np.uint8)
        colors[np.nonzero(shape)] = cls.COLOR
        return np.repeat(colors, 2, axis=1)


class J(Tetromino):
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
