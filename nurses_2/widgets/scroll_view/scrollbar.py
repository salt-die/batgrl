from typing import NamedTuple

from ...colors import BLACK, Color, color_pair
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class ScrollBarSettings(NamedTuple):
    bar_color: Color
    indicator_color: Color
    indicator_width: int  # This value doubled for horizontal scrollbars.
    # TODO: indicator_active_color, bar_active_color


# TODO: ButtonBehaviors instead of GrabbableBehavior -- To change color of bar and indicator when active.
class VerticalBar(GrabbableBehavior, Widget):
    def __init__(self, *args, settings: ScrollBarSettings, **kwargs):
        kwargs.pop('default_color_pair', None)
        bar_color, indicator_color, indicator_width = settings

        super().__init__(*args, default_color_pair=color_pair(BLACK, bar_color), **kwargs)

        self.indicator = Widget(
            dim=(indicator_width, 2),
            default_color_pair=color_pair(BLACK, indicator_color),
        )

        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.left = w - 2
        self.resize((h, 2))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.height - self.indicator.width - self.parent.show_horizontal_bar

    def render(self, canvas_view, colors_view, rect):
        self.indicator.top = round(self.parent.vertical_proportion * self.fill_width)
        super().render(canvas_view, colors_view, rect)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_y = mouse_event.position[0]

    def grab_update(self, mouse_event):
        dy = mouse_event.position[0] - self._last_y
        self._last_y = mouse_event.position[0]
        self.parent.vertical_proportion += dy / self.fill_width


class HorizontalBar(GrabbableBehavior, Widget):
    def __init__(self, *args, settings: ScrollBarSettings, **kwargs):
        kwargs.pop('default_color_pair', None)
        bar_color, indicator_color, indicator_width = settings

        super().__init__(*args, default_color_pair=color_pair(BLACK, bar_color), **kwargs)

        self.indicator = Widget(
            dim=(1, indicator_width << 1),
            default_color_pair=color_pair(BLACK, indicator_color),
        )

        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.top = h - 1
        self.resize((1, w))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.width - self.indicator.width - self.parent.show_vertical_bar * 2

    def render(self, canvas_view, colors_view, rect):
        self.indicator.left = round(self.parent.horizontal_proportion * self.fill_width)
        super().render(canvas_view, colors_view, rect)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self._last_x = mouse_event.position[1]

    def grab_update(self, mouse_event):
        dx = mouse_event.position[1] - self._last_x
        self._last_x = mouse_event.position[1]

        self.parent.horizontal_proportion += dx / self.fill_width
