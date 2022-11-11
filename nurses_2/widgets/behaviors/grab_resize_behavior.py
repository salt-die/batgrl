"""
Draggable resize behavior for a widget.
"""
from ...clamp import clamp
from ..graphic_widget import GraphicWidget, Size, AColor, TRANSPARENT
from ..widget import emitter
from .grabbable_behavior import GrabbableBehavior

__all__ = "GrabResizeBehavior",


class _Border(GrabbableBehavior, GraphicWidget):
    def __init__(self, y_edge, x_edge):
        super().__init__(disable_ptf=True)
        self.y_edge = y_edge
        self.x_edge = x_edge

    def grab_update(self, mouse_event):
        dy, dx = self.mouse_dyx
        y, x = self.to_local(mouse_event.position)

        if (
            dy < 0 and y >= self.height - 1
            or dy > 0 and y <= 0
            or dx < 0 and x >= self.width - 1
            or dx > 0 and x <= 0
        ):
            return

        parent = self.parent
        y_edge = parent.allow_vertical_resize and self.y_edge
        x_edge = parent.allow_horizontal_resize and self.x_edge

        h, w = parent.size

        new_size = Size(
            clamp(h + y_edge * dy, parent.grab_resize_min_height, None),
            clamp(w + x_edge * dx, parent.grab_resize_min_width, None),
        )

        if new_size != parent.size:
            parent.size = new_size

            if y_edge == - 1:
                parent.top += h - parent.height

            if x_edge == - 1:
                parent.left += w - parent.width

    def update_geometry(self):
        if self.parent is None:
            return

        h, w = self.parent.size
        bh, bw = self.parent.border_size

        match self.y_edge:
            case 0:
                height = h - 2 * bh
                top = bh
            case -1:
                height = bh
                top = 0
            case 1:
                height = bh
                top = h - bh

        match self.x_edge:
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
    Draggable resize behavior for a widget. Resize a widget by clicking its border
    and dragging it. Widget dimensions won't be resized smaller than :attr:`min_height`
    or :attr:`min_width`.

    Parameters
    ----------
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    grab_resize_min_height : int | None, default: None
        Minimum height widget can be resized by grabbing. Minimum
        height will never be less than `2 * border_size.height`.
    grab_resize_min_width : int | None, default: None
        Minimum width widget can be resized by grabbing. Minimum
        width will never be less than `2 * border_size.width`.
    border_alpha : float, default: 1.0
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor, default: TRANSPARENT
        Color of border.
    border_size : Size, default: Size(1, 2)
        Height and width of horizontal and vertical borders, respectively.

    Attributes
    ----------
    allow_vertical_resize : bool
        Allow vertical resize.
    allow_horizontal_resize : bool
        Allow horizontal resize.
    grab_resize_min_height : int
        Minimum height widget can be resized by grabbing.
    grab_resize_min_width : int
        Minimum width widget can be resized by grabbing.
    border_alpha : float
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor
        Color of border.
    border_size : Size
        Height and width of horizontal and vertical borders, respectively.

    Methods
    -------
    pull_border_to_front:
        Pull borders to the front.

    Notes
    -----
    Borders are added as child widgets. Children added later may overlap or cover the borders.
    :meth:`pull_border_to_front` will correct this.
    """
    def __init__(
        self,
        *,
        allow_vertical_resize: bool=True,
        allow_horizontal_resize: bool=True,
        grab_resize_min_height: int | None=None,
        grab_resize_min_width: int | None=None,
        border_alpha: float=1.0,
        border_color: AColor=TRANSPARENT,
        border_size: Size=Size(1, 2),
        **kwargs
    ):
        super().__init__(**kwargs)
        self._border_size = border_size

        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize

        self.grab_resize_min_height = grab_resize_min_height
        self.grab_resize_min_width = grab_resize_min_width

        borders = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        self._borders = tuple(_Border(*border) for border in borders)

        self.add_widgets(self._borders)

        self.border_alpha = border_alpha
        self.border_color = border_color
        self.border_size = border_size

    @property
    def grab_resize_min_height(self) -> int:
        return self._grab_resize_min_height

    @grab_resize_min_height.setter
    def grab_resize_min_height(self, min_height: int | None):
        h = 2 * self._border_size.height
        if min_height is None:
            self._grab_resize_min_height = h
        else:
            self._grab_resize_min_height = clamp(min_height, h, None)

    @property
    def grab_resize_min_width(self) -> int:
        return self._grab_resize_min_width

    @grab_resize_min_width.setter
    def grab_resize_min_width(self, min_width: int | None):
        w = 2 * self._border_size.width
        if min_width is None:
            self._grab_resize_min_width = w
        else:
            self._grab_resize_min_width = clamp(min_width, w, None)

    @property
    def border_size(self) -> Size:
        """
        Height and width of horizontal and vertical borders, respectively.
        """
        return self._border_size

    @border_size.setter
    @emitter
    def border_size(self, size: Size):
        h, w = size
        h = clamp(h, 1, None)
        w = clamp(w, 1, None)
        self._border_size = Size(h, w)
        self._grab_resize_min_height = max(2 * h, self._grab_resize_min_height)
        self._grab_resize_min_width = max(2 * w, self._grab_resize_min_width)

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
