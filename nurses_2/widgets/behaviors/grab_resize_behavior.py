from .grabbable_behavior import GrabbableBehavior
from ...data_structures import Size


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
    """
    def __init__(
        self,
        *,
        disable_ptf=False,
        allow_vertical_resize=True,
        allow_horizontal_resize=True,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.disable_ptf = disable_ptf
        self.allow_vertical_resize = allow_vertical_resize
        self.allow_horizontal_resize = allow_horizontal_resize

    def grab(self, mouse_event):
        self._bottom_edge = self.height - 1
        self._right_edge = self.width - 1

        match self.to_local(mouse_event.position):
            case (0, 0):
                self._grabbed_edge = -1, -1
            case (0, self._right_edge):
                self._grabbed_edge = -1,  1
            case (self._bottom_edge, 0):
                self._grabbed_edge =  1, -1
            case (self._bottom_edge, self._right_edge):
                self._grabbed_edge =  1,  1
            case (0, _):
                self._grabbed_edge = -1,  0
            case (self._bottom_edge, _):
                self._grabbed_edge =  1,  0
            case (_, 0):
                self._grabbed_edge =  0, -1
            case (_, self._right_edge):
                self._grabbed_edge =  0,  1
            case _:
                self._grabbed_edge = None
                return super().grab(mouse_event)

        self._is_grabbed = True

        if not self.disable_ptf:
            self.pull_to_front()

    def grab_update(self, mouse_event):
        if not self._grabbed_edge:
            return super().grab_update(mouse_event)

        y_edge, x_edge = self._grabbed_edge

        if not self.allow_vertical_resize:
            y_edge = 0

        if not self.allow_horizontal_resize:
            x_edge = 0

        h, w = self.size
        dy, dx = self.mouse_dyx

        new_size = Size(h + y_edge * dy, w + x_edge * dx)

        if new_size != self.size:
            self.resize(new_size)

            if y_edge < 0:
                self.top += dy

            if x_edge < 0:
                self.left += dx
