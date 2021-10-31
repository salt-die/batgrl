from typing import NamedTuple


class Point(NamedTuple):
    y: int
    x: int


class Size(NamedTuple):
    rows: int
    columns: int

    @property
    def height(self):
        return self.rows

    @property
    def width(self):
        return self.columns
