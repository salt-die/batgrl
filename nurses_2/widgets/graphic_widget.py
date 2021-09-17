from enum import IntEnum

import cv2
import numpy as np

from ..colors import BLACK_ON_BLACK
from ..data_structures import Point, Size
from .widget import Widget


class Interpolation(IntEnum):
    NEAREST = cv2.INTER_NEAREST
    LINEAR = cv2.INTER_LINEAR
    CUBIC = cv2.INTER_CUBIC
    AREA = cv2.INTER_AREA
    LANCZOS = cv2.INTER_LANCZOS4


class GraphicWidget(Widget):
    """
    Base for graphical widgets.
    """
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
        interpolation=Interpolation.LINEAR,
    ):
        self._size = size
        self.pos = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible
        self.is_enabled = is_enabled

        self.parent = None
        self.children = [ ]

        self.texture = np.full(
            (2 * self.height, self.width, 4),
            (*default_color_pair[:3], 1),
            dtype=np.uint8,
        )

        self.default_char = default_char
        self.default_color_pair = default_color_pair

        self.interpolation = interpolation

    def resize(self, size: Size):
        """
        Resize widget.
        """
        h, w = size
        self.texture = cv2.resize(
            self.texture,
            (w, 2 * h),
            interpolation=self.interpolation,
        )

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

        canvas_view[:] = self.default_char

        texture = self.texture
        even_rows = texture[2 * t: 2 * b: 2, l: r]
        odd_rows = texture[2 * t + 1: 2 * b: 2, l: r]

        foreground = colors_view[..., :3]
        background = colors_view[..., 3:]

        # RGBA on rgb == rgb + (RGB - rgb) * A
        even_buffer = np.subtract(even_rows[..., :3], foreground, dtype=np.float16)
        odd_buffer = np.subtract(odd_rows[..., :3], background, dtype=np.float16)

        np.multiply(even_buffer, even_rows[..., 3], out=even_buffer)
        np.multiply(odd_buffer, odd_rows[..., 3], out=odd_buffer)

        np.add(even_buffer, foreground, out=foreground, casting="unsafe")
        np.add(odd_buffer, background, out=background, casting="unsafe")
