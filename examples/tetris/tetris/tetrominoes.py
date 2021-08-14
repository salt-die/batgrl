from enum import IntFlag

import numpy as np

from .wall_kicks import *
from .color_scheme import *


class Orientation(IntFlag):
    """
    Orientation of a tetromino.
    """
    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    def rotate(self, clockwise=True):
        return Orientation((self + (1 if clockwise else -1)) % 4)


def create_canvas(shape):
    """
    Return a nurses_2 widget canvas from a tetromino shape.
    """
    return np.repeat(np.where(shape, "▀", " "), 2, axis=1,)

def create_colors(shape, color):
    """
    Return a nurses_2 widget colors array from a tetromino shape and color.
    """
    colors = np.zeros((*shape.shape, 6), dtype=np.uint8)
    colors[shape == 1] = *color, *color
    return np.repeat(colors, 2, axis=1)


class Tetromino:
    def __init_subclass__(cls):
        base = np.array(cls.BASE_SHAPE, dtype=np.uint8)

        cls.shapes = {
            Orientation.UP:    base,
            Orientation.RIGHT: np.rot90(base, 3),
            Orientation.DOWN:  np.rot90(base, 2),
            Orientation.LEFT:  np.rot90(base, 1),
        }

        cls.mino_positions = {
            orientation: np.argwhere(shape) for orientation, shape in cls.shapes.items()
        }

        cls.canvases = {
            orientation: create_canvas(shape) for orientation, shape in cls.shapes.items()
        }

        cls.colors = {
            orientation: create_colors(shape, cls.COLOR) for orientation, shape in cls.shapes.items()
        }


class J(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [1, 0, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = J_COLOR


class L(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 0, 1],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = L_COLOR


class S(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 1, 1],
        [1, 1, 0],
        [0, 0, 0],
    ]
    COLOR = S_COLOR


class T(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [0, 1, 0],
        [1, 1, 1],
        [0, 0, 0],
    ]
    COLOR = T_COLOR


class Z(Tetromino):
    WALL_KICKS = JLSTZ_WALL_KICKS
    BASE_SHAPE = [
        [1, 1, 0],
        [0, 1, 1],
        [0, 0, 0],
    ]
    COLOR = Z_COLOR


class I(Tetromino):
    WALL_KICKS = I_WALL_KICKS
    BASE_SHAPE = [
        [0, 0, 0, 0],
        [1, 1, 1, 1],
        [0, 0, 0, 0],
        [0, 0, 0, 0],
    ]
    COLOR = I_COLOR


class ArikaI(Tetromino):
    WALL_KICKS = ARIKA_I_WALL_KICKS
    BASE_SHAPE = I.BASE_SHAPE
    COLOR = I_COLOR


class O(Tetromino):
    WALL_KICKS = O_WALL_KICKS
    BASE_SHAPE = [
        [1, 1],
        [1, 1],
    ]
    COLOR = O_COLOR


TETROMINOS = J, L, S, T, Z, I, O,
ARIKA_TETROMINOS = J, L, S, T, Z, ArikaI, O,
