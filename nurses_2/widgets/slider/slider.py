from typing import Optional, Callable

from ...colors import Color
from ...utils import clamp
from ..widget import Widget
from ..widget_data_structures import Point
from .handle import _Handle


class Slider(Widget):
    """
    A slider widget.

    Parameters
    ----------
    width : int
        Width of the slider.
    pos : Point, default: Point(0, 0)
        Top-left location of the slider.
    min : float
        Minimum value.
    max : float
        Maximum value.
    proportion : float, default: 0.0
        Starting proportion of slider.
    handle_color : Color
        Color of slider handle.
    slider_enabled : bool, default: True
        Allow dragging handle.
    callback : Optional[Callable], default: None
        Single argument callable that takes the new value of slider, when slider
        value is updated.
    """
    def __init__(
        self,
        width: int,
        pos: Point=Point(0, 0),
        *,
        min,
        max,
        proportion=0.0,
        handle_color: Color,
        slider_enabled=True,
        callback: Optional[Callable]=None,
        default_char="=",
        **kwargs,
        ):
        super().__init__(dim=(1, width), pos=pos, default_char=default_char, **kwargs)

        assert min < max
        self.min = min
        self.max = max

        self.slider_enabled = slider_enabled
        self.callback = callback
        self._proportion = 0

        self.add_widget(_Handle(handle_color))
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

            handle = self.children[0]
            handle.update_geometry()

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        if self.callback is not None:
            self.callback(value)
