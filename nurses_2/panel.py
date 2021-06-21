import numpy as np
from prompt_toolkit.styles import DEFAULT_ATTRS


class Panel:
    """Stackable windows.
    """
    __slots__ = (
        "content",
        "attrs",
        "top",
        "left",
        "z",
        "default_char",
        "default_attr",
        "is_transparent",
        "is_visible",
    )

    def __init__(self, dim, pos=(0, 0), *, z=0, default_char=" ", default_attr=DEFAULT_ATTRS, is_transparent=False, is_visible=True):
        assert len(default_char) == 1, f'expected single character, got {default_char!r}'

        self.content = np.full(dim, default_char, dtype=object)
        self.attrs = np.full(dim, None, dtype=object)
        self.attrs[:] = ((DEFAULT_ATTRS, ), )

        self.top, self.left = pos

        self.z = z
        self.default_char = default_char
        self.default_attr = default_attr
        self.is_transparent = is_transparent
        self.is_visible = is_visible

    @property
    def dim(self):
        return self.content.shape

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
