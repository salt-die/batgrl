from typing import Callable

from ...clamp import clamp
from ...colors import Color
from ...data_structures import Point
from ...io import MouseEventType
from ..text_widget import TextWidget
from .handle import _Handle


class Slider(TextWidget):
    """
    A slider widget.

    Parameters
    ----------
    width : int
        Width of the slider.
    min : float
        Minimum value.
    max : float
        Maximum value.
    pos : Point, default: Point(0, 0)
        Top-left location of the slider.
    proportion : float, default: 0.0
        Starting proportion of slider.
    handle_color : Color | None, default: None
        Color of slider handle. If None, handle color is `default_fg_color`.
    fill_color: Color | None, default: None
        Color of "filled" portion of slider.
    slider_enabled : bool, default: True
        Allow dragging handle.
    callback : Callable | None, default: None
        Single argument callable called with new value of slider when slider is updated.
    """
    def __init__(
        self,
        *,
        width: int,
        min: float,
        max: float,
        pos: Point=Point(0, 0),
        proportion=0.0,
        handle_color: Color | None=None,
        fill_color: Color | None=None,
        slider_enabled=True,
        callback: Callable | None=None,
        default_char="▬",
        **kwargs,
        ):
        super().__init__(size=(1, width), pos=pos, default_char=default_char, **kwargs)

        if min >= max:
            raise ValueError(f"{min=} >= {max=}")

        self.min = min
        self.max = max

        self.slider_enabled = slider_enabled
        self.callback = callback
        self._proportion = 0

        self.fill_color = fill_color or self.default_fg_color

        self.handle = _Handle(color=handle_color or self.default_fg_color)
        self.add_widget(self.handle)
        self.proportion = proportion

    @property
    def proportion(self):
        return self._proportion

    @proportion.setter
    def proportion(self, value):
        if self.slider_enabled:
            self._proportion = clamp(value, 0, 1)

            min, max = self.min, self.max
            self.value = (max - min) * self._proportion + min

            self.handle.update_geometry()
            handle_x = self.handle.x
            self.colors[:, :handle_x, :3] = self.fill_color
            self.colors[:, handle_x:, :3] = self.default_fg_color


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self.callback is not None:
            self.callback(value)

    @property
    def fill_width(self):
        """
        Width of the slider minus the width of the handle.
        """
        return self.width - self.handle.width

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_point(mouse_event.position)
        ):
            x = self.to_local(mouse_event.position).x

            self.proportion = x / self.fill_width
            self.handle.grab(mouse_event)

            return True
