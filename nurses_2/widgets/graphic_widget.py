from enum import IntEnum

import cv2
import numpy as np

from ..clamp import clamp
from ..colors import AColor, TRANSPARENT
from ..data_structures import *
from .widget_data_structures import *
from ._widget_base import _WidgetBase


class Interpolation(IntEnum):
    NEAREST = cv2.INTER_NEAREST
    LINEAR = cv2.INTER_LINEAR
    CUBIC = cv2.INTER_CUBIC
    AREA = cv2.INTER_AREA
    LANCZOS = cv2.INTER_LANCZOS4


class GraphicWidget(_WidgetBase):
    """
    Base for graphic widgets.

    Graphic widgets are widgets that are rendered entirely with the upper half block character, "▀".
    Graphic widgets' color information is stored in a uint8 RGBA array, `texture`.

    Parameters
    ----------
    size : Size, default: Size(10, 10)
        Size of widget.
    pos : Point, default: Point(0, 0)
        Position of upper-left corner in parent.
    size_hint : SizeHint, default: SizeHint(None, None)
        Proportion of parent's height and width. Non-None values will have
        precedent over `size`.
    pos_hint : PosHint, default: PosHint(None, None)
        Position as a proportion of parent's height and width. Non-None values
        will have precedent over `pos`.
    anchor : Anchor, default: Anchor.TOP_LEFT
        Specifies which part of the widget is aligned with the `pos_hint`.
    is_transparent : bool, default: True
        If False the underlying texture's alpha channel is ignored.
    is_visible : bool, default: True
        If false, widget won't be painted, but still dispatched.
    is_enabled : bool, default: True
        If false, widget won't be painted or dispatched.
    default_color : AColor, default: AColor(0, 0, 0, 0)
        Default texture color.
    alpha : float, default: 1.0
        If widget is transparent, the alpha channel of the underlying texture will be multiplied by this
        value. (0 <= alpha <= 1.0)
    interpolation : Interpolation, default: Interpolation.LINEAR
        The interpolation used when resizing the GraphicWidget.
    """
    def __init__(
        self,
        is_transparent: bool=True,
        default_color: AColor=TRANSPARENT,
        alpha: float=1.0,
        interpolation: Interpolation=Interpolation.LINEAR,
        **kwargs,
    ):
        super().__init__(is_transparent=is_transparent, **kwargs)

        self.default_color = default_color
        self.interpolation = interpolation
        self.alpha = clamp(alpha, 0, 1.0)

        h, w = self.size
        self.texture = np.full(
            (2 * h, w, 4),
            default_color,
            dtype=np.uint8,
        )

    def resize(self, size: Size):
        """
        Resize widget.
        """
        h, w = size
        self._size = Size(h, w)

        self.texture = cv2.resize(
            self.texture,
            (w, 2 * h),
            interpolation=self.interpolation,
        )

        for child in self.children:
            child.update_geometry()

    def render(self, canvas_view, colors_view, source_slice: tuple[slice, slice]):
        """
        Paint region given by source_slice into canvas_view and colors_view.
        """
        vert_slice, hori_slice = source_slice
        t = vert_slice.start
        b = vert_slice.stop

        canvas_view[:] = "▀"

        alpha = self.alpha

        texture = self.texture
        even_rows = texture[2 * t: 2 * b: 2, hori_slice]
        odd_rows = texture[2 * t + 1: 2 * b: 2, hori_slice]

        foreground = colors_view[..., :3]
        background = colors_view[..., 3:]

        if not self.is_transparent:
            foreground[:] = even_rows[..., :3]
            background[:] = odd_rows[..., :3]
        else:
            even_buffer = np.subtract(even_rows[..., :3], foreground, dtype=float)
            odd_buffer = np.subtract(odd_rows[..., :3], background, dtype=float)

            np.multiply(even_buffer, even_rows[..., 3, None], out=even_buffer)
            np.multiply(even_buffer, alpha, out=even_buffer)
            np.divide(even_buffer, 255, out=even_buffer)

            np.multiply(odd_buffer, odd_rows[..., 3, None], out=odd_buffer)
            np.multiply(odd_buffer, alpha, out=odd_buffer)
            np.divide(odd_buffer, 255, out=odd_buffer)

            np.add(even_buffer, foreground, out=foreground, casting="unsafe")
            np.add(odd_buffer, background, out=background, casting="unsafe")

        self.render_children(source_slice, canvas_view, colors_view)
