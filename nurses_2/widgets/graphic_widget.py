from pathlib import Path

import cv2
import numpy as np

from ..clamp import clamp
from ..colors import AColor, TRANSPARENT
from ..data_structures import *
from .graphic_widget_data_structures import *
from .widget_base import WidgetBase
from .widget_data_structures import *

class GraphicWidget(WidgetBase):
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
    min_height : int | None, default: None
        Minimum height set due to size_hint. Ignored if corresponding size
        hint is None.
    max_height : int | None, default: None
        Maximum height set due to size_hint. Ignored if corresponding size
        hint is None.
    min_width : int | None, default: None
        Minimum width set due to size_hint. Ignored if corresponding size
        hint is None.
    max_width : int | None, default: None
        Maximum width set due to size_hint. Ignored if corresponding size
        hint is None.
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
        self.alpha = alpha

        h, w = self.size
        self.texture = np.full(
            (2 * h, w, 4),
            default_color,
            dtype=np.uint8,
        )

    @property
    def alpha(self):
        return self._alpha

    @alpha.setter
    def alpha(self, alpha: float):
        self._alpha = clamp(float(alpha), 0.0, 1.0)

    def resize(self, size: Size):
        """
        Resize widget.
        """
        h, w = size
        self._size = Size(h, w)

        if h == 0 or w == 0:
            self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)
        else:
            self.texture = cv2.resize(
                self.texture,
                (w, 2 * h),
                interpolation=self.interpolation,
            )

        for child in self.children:
            child.update_geometry()

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        """
        Paint region given by source into canvas_view and colors_view.
        """
        vert_slice, hori_slice = source
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

        self.render_children(source, canvas_view, colors_view)

    def to_png(self, path: Path):
        BGRA = cv2.cvtColor(self.texture, cv2.COLOR_RGBA2BGRA)
        cv2.imwrite(str(path.absolute()), BGRA)
