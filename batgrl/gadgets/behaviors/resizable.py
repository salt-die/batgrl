"""Draggable resize behavior for a gadget."""
from ..graphics import TRANSPARENT, AColor, Graphics, Size, clamp
from .grabbable import Grabbable

__all__ = ["Resizable"]


class _Border(Grabbable, Graphics):
    def __init__(self, y_edge, x_edge):
        super().__init__(size=(1, 2), disable_ptf=True)
        self.y_edge = y_edge
        self.x_edge = x_edge

    def grab_update(self, mouse_event):
        dy, dx = self.mouse_dyx
        y, x = self.to_local(mouse_event.position)

        if (
            dy < 0
            and y >= self.height - 1
            or dy > 0
            and y <= 0
            or dx < 0
            and x >= self.width - 1
            or dx > 0
            and x <= 0
        ):
            return

        parent = self.parent
        y_edge = parent.allow_vertical_resize and self.y_edge
        x_edge = parent.allow_horizontal_resize and self.x_edge

        h, w = parent.size

        new_size = Size(
            clamp(h + y_edge * dy, parent.resize_min_height, None),
            clamp(w + x_edge * dx, parent.resize_min_width, None),
        )

        if new_size != parent.size:
            parent.size = new_size

            if y_edge == -1:
                parent.top += h - parent.height

            if x_edge == -1:
                parent.left += w - parent.width

    def _update_size_pos(self):
        h, w = self.parent.size

        if self.y_edge == -1:
            height = 1
            top = 0
        elif self.y_edge == 0:
            height = h - 2
            top = 1
        else:
            height = 1
            top = h - 1

        if self.x_edge == -1:
            width = 2
            left = 0
        elif self.x_edge == 0:
            width = w - 4
            left = 2
        else:
            width = 2
            left = w - 2

        self.pos = top, left
        self.size = height, width

    def on_add(self):
        super().on_add()
        self._update_size_pos()
        self.subscribe(self.parent, "size", self._update_size_pos)

    def on_remove(self):
        self.unsubscribe(self.parent, "size")
        super().on_remove()


class Resizable:
    """
    Draggable resize behavior for a gadget. Resize a gadget by clicking its border and
    dragging it. Gadget dimensions won't be resized smaller than
    :attr:`resize_min_height` or :attr:`resize_min_width`.

    Parameters
    ----------
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    resize_min_height : int | None, default: None
        Minimum height gadget can be resized by grabbing.
    resize_min_width : int | None, default: None
        Minimum width gadget can be resized by grabbing.
    border_alpha : float, default: 1.0
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor, default: TRANSPARENT
        Color of border.

    Attributes
    ----------
    allow_vertical_resize : bool
        Allow vertical resize.
    allow_horizontal_resize : bool
        Allow horizontal resize.
    resize_min_height : int
        Minimum height gadget can be resized by grabbing.
    resize_min_width : int
        Minimum width gadget can be resized by grabbing.
    border_alpha : float
        Transparency of border. This value will be clamped between `0.0` and `1.0`.
    border_color : AColor
        Color of border.

    Methods
    -------
    pull_border_to_front():
        Pull borders to the front.

    Notes
    -----
    Borders are added as child gadgets. Children added later may overlap or cover the
    borders. :meth:`pull_border_to_front` will correct this.
    """

    def __init__(
        self,
        *,
        allow_vertical_resize: bool = True,
        allow_horizontal_resize: bool = True,
        resize_min_height: int | None = None,
        resize_min_width: int | None = None,
        border_alpha: float = 1.0,
        border_color: AColor = TRANSPARENT,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize

        self.resize_min_height = resize_min_height
        self.resize_min_width = resize_min_width

        borders = ((-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1))
        self._borders = tuple(_Border(*border) for border in borders)

        self.add_gadgets(self._borders)

        self.border_alpha = border_alpha
        self.border_color = border_color

    @property
    def resize_min_height(self) -> int:
        """Minimum height gadget can be resized by grabbing."""
        return self._resize_min_height

    @resize_min_height.setter
    def resize_min_height(self, min_height: int | None):
        if min_height is None:
            self._resize_min_height = 2
        else:
            self._resize_min_height = clamp(min_height, 2, None)

    @property
    def resize_min_width(self) -> int:
        """Minimum width gadget can be resized by grabbing."""
        return self._resize_min_width

    @resize_min_width.setter
    def resize_min_width(self, min_width: int | None):
        if min_width is None:
            self._resize_min_width = 4
        else:
            self._resize_min_width = clamp(min_width, 4, None)

    @property
    def border_alpha(self) -> float:
        """Border transparency."""
        return self._border_alpha

    @border_alpha.setter
    def border_alpha(self, border_alpha: float):
        border_alpha = clamp(border_alpha, 0.0, 1.0)
        for border in self._borders:
            border.alpha = border_alpha

        self._border_alpha = border_alpha

    @property
    def border_color(self) -> AColor:
        """Color of border."""
        return self._border_color

    @border_color.setter
    def border_color(self, border_color: AColor):
        for border in self._borders:
            border.default_color = border_color
            border.texture[:] = border_color

        self._border_color = border_color

    def pull_border_to_front(self):
        """Pull borders to the front."""
        for border in self._borders:
            border.pull_to_front()
