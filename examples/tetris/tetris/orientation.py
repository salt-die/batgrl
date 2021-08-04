from enum import IntFlag


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
