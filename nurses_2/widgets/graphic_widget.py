import numpy as np

from ..colors import BLACK_ON_BLACK
from ..data_structures import Point, Size
from .widget import Widget


class GraphicWidget(Widget):
    def __init__(
        self,
        size: Size=Size(10, 10),
        pos: Point=Point(0, 0),
        *,
        is_transparent=False,
        is_visible=True,
        is_enabled=True,
        default_char="▀",
        default_color_pair=BLACK_ON_BLACK,
    ):
        self._size = size
        self.pos = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

        self.parent = None
        self.children = [ ]

        self.texture = np.full((2 * self.height, self.width, 3), default_color_pair[:3], dtype=np.uint8)

        self.default_char = default_char
        self.default_color_pair = default_color_pair

    def resize(self, size: Size):
        """
        Resize widget.
        """
        raise NotImplementedError

        for child in self.children:
            child.update_geometry()

    def normalize_canvas(self):
        raise NotImplementedError

    def get_view(self):
        raise NotImplementedError

    def render(self, canvas_view, colors_view, rect: Rect):
        """
        Paint region given by rect into canvas_view and colors_view.
        """
        t, l, b, r, _, _ = rect

        index_rect = slice(t, b), slice(l, r)

        raise NotImplementedError
