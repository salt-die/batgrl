class Band:
    """
    A vertical interval and a list of walls.
    """
    __slots__ = "top", "bottom", "walls"

    def __init__(self, top, bottom, walls: list[int] | None=None):
        self.top = top
        self.bottom = bottom
        self.walls = walls or [ ]

    @property
    def slices(self):
        """
        Yield slices that make up the band.
        """
        topbottom = slice(self.top, self.bottom)

        it = iter(self.walls)
        for left, right in zip(it, it):
            yield topbottom, slice(left, right)

    def split(self, n: int):
        """
        Split band along the horizontal line at n.
        A new band is returned for the bottom portion of the split.
        """
        try:
            return Band(n, self.bottom, self.walls.copy())
        finally:
            self.bottom = n

    def divmod(self, other):
        inside_self = inside_other = False
        inside_div = inside_mod = False

        self_walls = iter(self.walls)
        other_walls = iter(other.walls)

        self_wall = next(self_walls, None)
        other_wall = next(other_walls, None)

        div_walls = [ ]
        mod_walls = [ ]

        while self_wall is not None or other_wall is not None:
            match (self_wall, other_wall):
                case (None, _):
                    threshold = other_wall
                case (_, None):
                    threshold = self_wall
                case _:
                    threshold = min(self_wall, other_wall)

            if self_wall == threshold:
                inside_self ^= True
                self_wall = next(self_walls, None)

            if other_wall == threshold:
                inside_other ^= True
                other_wall = next(other_walls, None)

            if (inside_self and inside_other) != inside_div:
                inside_div ^= True
                div_walls.append(threshold)

            if (inside_self and not inside_other) != inside_mod:
                inside_mod ^= True
                mod_walls.append(threshold)

        other.walls = div_walls
        self.walls = mod_walls

    def __repr__(self):
        attrs = ', '.join(
            f'{attr}={getattr(self, attr)}'
            for attr in self.__slots__
        )
        return f'{type(self).__name__}({attrs})'