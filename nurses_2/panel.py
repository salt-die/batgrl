import numpy as np


class Panel:
    """Stackable windows.
    """
    def __init__(self, dim, pos=(0, 0), *, z=0, background=" ", color="", is_transparent=False, is_visible=True):
        assert len(background) == 1, f'expected single character, got {background!r}'

        self.content = np.full(dim, background, dtype=object)
        self.colors = np.full(dim, color, dtype=object)

        self.top, self.left = pos

        self.z = z
        self.background = background
        self.color = color
        self.is_transparent = transparent
        self.is_visible = hidden

    @property
    def height(self):
        return self.content.shape[0]

    @property
    def width(self):
        return self.content.shape[1]

    @property
    def bottom(self):
        return self.top + self.height

    @property
    def right(self):
        return self.left + self.width

    @property
    def middle(self):
        return self.height // 2, self.width // 2

    def __lt__(self, other):
        return self.z < other.z
