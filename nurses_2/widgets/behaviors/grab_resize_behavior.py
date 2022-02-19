from ...clamp import clamp
from ...data_structures import Size
from .grabbable_behavior import GrabbableBehavior


class GrabResizeBehavior(GrabbableBehavior):
    """
    Draggable resize behavior for a widget. Resize a widget by clicking its border and dragging it.

    Parameters
    ----------
    disable_ptf : bool, default: False
        If True, widget will not be pulled to front when grabbed.
    allow_vertical_resize : bool, default: True
        Allow vertical resize.
    allow_horizontal_resize : bool, default: True
        Allow horizontal resize.
    min_height : int, default: 2
        Minimum height allowed by grab resizing.
    max_height : int | None, default: None
        Maximum height allowed by grab resizing.
    min_width : int, default: 4
        Minimum width allowed by grab resizing.
    max_width : int | None, default: None
        Maximum width allowed by grab resizing.

    Notes
    -----
    `min_height`, `max_height`, `min_width`, and `max_width` are repurposed from WidgetBase for
    grab resize behavior as size hints are expected to be None for widgets that inherit this behavior.
    If a widget has a non-None size hint and inherits this behavior, these attributes will still work
    as expected.
    """
    def __init__(
        self,
        *,
        disable_ptf=False,
        allow_vertical_resize=True,
        allow_horizontal_resize=True,
        min_height=2,
        max_height=None,
        min_width=4,
        max_width=None,
        **kwargs
    ):
        super().__init__(
            min_height=min_height,
            max_height=max_height,
            min_width=min_width,
            max_width=max_width,
            **kwargs,
        )
        self.disable_ptf = disable_ptf
        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize

    def grab(self, mouse_event):
        self._b_edge = self.height - 1
        self._r_edge = self.width - 1
        self._r_r_edge = self.width - 2

        match self.to_local(mouse_event.position):
            case (0, 0 | 1):
                self._grabbed_edge = -1, -1
            case (0, self._r_edge | self._r_r_edge):
                self._grabbed_edge = -1,  1
            case (self._b_edge, 0 | 1):
                self._grabbed_edge =  1, -1
            case (self._b_edge, self._r_edge | self._r_r_edge):
                self._grabbed_edge =  1,  1
            case (0, _):
                self._grabbed_edge = -1,  0
            case (self._b_edge, _):
                self._grabbed_edge =  1,  0
            case (_, 0 | 1):
                self._grabbed_edge =  0, -1
            case (_, self._r_edge | self._r_r_edge):
                self._grabbed_edge =  0,  1
            case _:
                self._grabbed_edge = None
                return super().grab(mouse_event)

        self._is_grabbed = True

        if not self.disable_ptf:
            self.pull_to_front()

    def grab_update(self, mouse_event):
        if self._grabbed_edge is None:
            return super().grab_update(mouse_event)

        y_edge, x_edge = self._grabbed_edge

        if not self.allow_vertical_resize:
            y_edge = 0

        if not self.allow_horizontal_resize:
            x_edge = 0

        h, w = self.size
        dy, dx = self.mouse_dyx

        new_size = Size(
            clamp(h + y_edge * dy, self.min_height, self.max_height),
            clamp(w + x_edge * dx, self.min_width, self.max_width),
        )

        if new_size != self.size:
            self.resize(new_size)

            if y_edge < 0:
                self.top += h - new_size.height

            if x_edge < 0:
                self.left += w - new_size.width
