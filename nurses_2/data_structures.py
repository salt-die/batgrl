from typing import NamedTuple


class Point(NamedTuple):
    y: int
    x: int


class Size(NamedTuple):
    height: int
    width: int

    @property
    def rows(self):
        return self.height

    @property
    def columns(self):
        return self.width
