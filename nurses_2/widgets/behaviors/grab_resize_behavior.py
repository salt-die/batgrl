from ...clamp import clamp
from ..graphic_widget import GraphicWidget, Size, AColor, TRANSPARENT
from .grabbable_behavior import GrabbableBehavior

__all__ = "GrabResizeBehavior",


class _Border(GrabbableBehavior, GraphicWidget):
    def __init__(self, y_edge, x_edge, disable_ptf=True, **kwargs):
        super().__init__(disable_ptf=disable_ptf, **kwargs)

        self.y_edge = y_edge
        self.x_edge = x_edge

    def grab_update(self, mouse_event):
        parent = self.parent
        y_edge = parent.allow_vertical_resize and self.y_edge
        x_edge = parent.allow_horizontal_resize and self.x_edge

        h, w = parent.size
        dy, dx = self.mouse_dyx

        new_size = Size(
            clamp(h + y_edge * dy, parent.min_height, None),
            clamp(w + x_edge * dx, parent.min_width, None),
        )

        if new_size != self.size:
            parent.resize(new_size)

            if y_edge < 0:
                parent.top += h - new_size.height

            if x_edge < 0:
                parent.left += w - new_size.width

    def update_geometry(self):
        if self.parent is None:
            return

        h, w = self.parent.size
        bh, bw = self.parent.border_size
        y, x = self.y_edge, self.x_edge

        self.pos = 0 if y <= 0 else h - 1, 0 if x <= 0 else w - 1

        match y:
            case 0:
                height = h - 2 * bh
                top = bh
            case -1:
                height = bh
                top = 0
            case 1:
                height = bh
                top = h - bh

        match x:
            case 0:
                width = w - 2 * bw
                left = bw
            case -1:
                width = bw
                left = 0
            case 1:
                width = bw
                left = w - bw

        self.pos = top, left
        self.size = height, width


class GrabResizeBehavior:
    """
    Draggable resize behavior for a widget. Resize a widget by clicking its border and dragging it.
    Widget dimensions won't be resized smaller than `min_height` or `min_width`.

    Notes
    -----
    Borders are added as child widgets. Children added later may overlap or cover the borders.
    The method `pull_border_to_front` will correct this.

    Parameters
    ----------
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    border_alpha : float, default: 1.0
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor, default: TRANSPARENT
        Color of border.
    border_size : Size, default: Size(1, 2)
        Height and width of horizontal and vertical borders, respectively.
    """
    def __init__(
        self,
        *,
        allow_vertical_resize: bool=True,
        allow_horizontal_resize: bool=True,
        border_alpha: float=1.0,
        border_color: AColor=TRANSPARENT,
        border_size: Size=Size(1, 2),
        **kwargs
    ):
        super().__init__(**kwargs)

        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize

        # Sides
        top = _Border(-1, 0)
        bottom = _Border(1, 0)
        left = _Border(0, -1)
        right = _Border(0, 1)

        # Corners
        top_left = _Border(-1, -1)
        top_right = _Border(-1, 1)
        bottom_left = _Border(1, -1)
        bottom_right = _Border(1, 1)

        self._borders = top, bottom, left, right, top_left, top_right, bottom_left, bottom_right

        self.border_alpha = border_alpha
        self.border_color = border_color
        self.border_size = border_size

        self.add_widgets(self._borders)

    @property
    def border_size(self) -> Size:
        """
        Height and width of horizontal and vertical borders, respectively.
        """
        return self._border_size

    @border_size.setter
    def border_size(self, size: Size):
        h, w = size
        self._border_size = Size(clamp(h, 1, None), clamp(w, 1, None))

        for border in self._borders:
            border.update_geometry()

    @property
    def border_alpha(self) -> float:
        """
        Background character of the border.
        """
        return self._border_alpha

    @border_alpha.setter
    def border_alpha(self, border_alpha: float):
        border_alpha = clamp(border_alpha, 0.0, 1.0)
        for border in self._borders:
            border.alpha = border_alpha

        self._border_alpha = border_alpha

    @property
    def border_color(self) -> AColor:
        """
        Color of border.
        """
        return self._border_color

    @border_color.setter
    def border_color(self, border_color: AColor):
        for border in self._borders:
            border.default_color = border_color
            border.texture[:] = border_color

        self._border_color = border_color

    def pull_border_to_front(self):
        for border in self._borders:
            border.pull_to_front()
