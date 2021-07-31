from typing import NamedTuple

from ...colors import Color
from ...mouse.mouse_event import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class ScrollBarSettings(NamedTuple):
    bar_color: Color
    indicator_color: Color
    indicator_width: int  # Should be even.
    # TODO: indicator_active_color, bar_active_color


# TODO: Widget-fy the indicator. (And then we can remove render methods.)
class VerticalBar(GrabbableBehavior, Widget):
    def __init__(self, *args, settings: ScrollBarSettings, **kwargs):
        self.settings = settings
        super().__init__(*args, **kwargs)

    def update_geometry(self):
        h, w = self.parent.dim

        self.left = w - 2
        self.resize((h, 2))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.height - self.settings.indicator_width // 2 - self.parent.show_horizontal_bar

    def render(self, canvas_view, colors_view, rect):
        start_fill = round(self.parent.vertical_proportion * self.fill_width)
        bar_color, indicator_color, indicator_width = self.settings

        self.colors[:, :, 3:] = bar_color
        self.colors[start_fill: start_fill + indicator_width // 2, :, 3:] = indicator_color

        super().render(canvas_view, colors_view, rect)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_y = mouse_event.position[0]

    def grab_update(self, mouse_event):
        dy = mouse_event.position[0] - self._last_y
        self._last_y = mouse_event.position[0]
        self.parent.vertical_proportion += dy / self.fill_width


class HorizontalBar(GrabbableBehavior, Widget):
    def __init__(self, settings: ScrollBarSettings, **kwargs):
        self.settings = settings
        super().__init__(**kwargs)

    def update_geometry(self):
        h, w = self.parent.dim

        self.top = h - 1
        self.resize((1, w))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.width - self.settings.indicator_width - self.parent.show_vertical_bar * 2

    def render(self, canvas_view, colors_view, rect):
        start_fill = round(self.parent.horizontal_proportion * self.fill_width)
        bar_color, indicator_color, indicator_width = self.settings

        self.colors[0, :, 3:] = bar_color
        self.colors[0, start_fill: start_fill + indicator_width, 3:] = indicator_color

        super().render(canvas_view, colors_view, rect)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_x = mouse_event.position[1]

    def grab_update(self, mouse_event):
        dx = mouse_event.position[1] - self._last_x
        self._last_x = mouse_event.position[1]

        self.parent.horizontal_proportion += dx / self.fill_width
