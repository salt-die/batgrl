from enum import IntFlag

import numpy as np
from batgrl.colors import Color

from .wall_kicks import ARIKA_I_WALL_KICKS, I_WALL_KICKS, JLSTZ_WALL_KICKS, O_WALL_KICKS


class Orientation(IntFlag):
    """Orientation of a tetromino."""

    UP = 0
    RIGHT = 1
    DOWN = 2
    LEFT = 3

    def rotate(self, clockwise=True):
        return Orientation((self + (1 if clockwise else -1)) % 4)


class Tetromino:
    def __init__(self, base, color, kicks):
        base = np.array(base, dtype=np.uint8)
        self.shapes = {
            Orientation.UP: base,
            Orientation.RIGHT: np.rot90(base, 3),
            Orientation.DOWN: np.rot90(base, 2),
            Orientation.LEFT: np.rot90(base, 1),
        }
        self.mino_positions = {
            orientation: np.argwhere(shape)
            for orientation, shape in self.shapes.items()
        }

        self.textures = {}
        for orientation, shape in self.shapes.items():
            texture = np.repeat(
                np.kron(shape, np.ones((2, 2), int))[..., None], 4, axis=-1
            )
            texture *= (*color, 255)
            self.textures[orientation] = texture

        self.kicks = kicks


J = Tetromino(
    [[1, 0, 0], [1, 1, 1], [0, 0, 0]], Color.from_hex("130bea"), JLSTZ_WALL_KICKS
)
L = Tetromino(
    [[0, 0, 1], [1, 1, 1], [0, 0, 0]], Color.from_hex("f46e07"), JLSTZ_WALL_KICKS
)
S = Tetromino(
    [[0, 1, 1], [1, 1, 0], [0, 0, 0]], Color.from_hex("0fea0b"), JLSTZ_WALL_KICKS
)
T = Tetromino(
    [[0, 1, 0], [1, 1, 1], [0, 0, 0]], Color.from_hex("6900d3"), JLSTZ_WALL_KICKS
)
Z = Tetromino(
    [[1, 1, 0], [0, 1, 1], [0, 0, 0]], Color.from_hex("f92504"), JLSTZ_WALL_KICKS
)
I = Tetromino(  # noqa: E741
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    Color.from_hex("10f2e3"),
    I_WALL_KICKS,
)
ARIKA_I = Tetromino(
    [[0, 0, 0, 0], [1, 1, 1, 1], [0, 0, 0, 0], [0, 0, 0, 0]],
    Color.from_hex("10f2e3"),
    ARIKA_I_WALL_KICKS,
)
O = Tetromino([[1, 1], [1, 1]], Color.from_hex("eded0e"), O_WALL_KICKS)  # noqa: E741

TETROMINOS = J, L, S, T, Z, I, O
ARIKA_TETROMINOS = J, L, S, T, Z, ARIKA_I, O
