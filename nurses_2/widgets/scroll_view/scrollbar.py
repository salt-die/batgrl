from typing import NamedTuple

from ...colors import Color
from ...mouse.mouse_event import MouseEventType
from ..widget import Widget


class ScrollBarSettings(NamedTuple):
    bar_color: Color
    indicator_color: Color
    indicator_width: int  # Should be even.


class VerticalBar(Widget):
    def __init__(self, *args, scrollbar_settings: ScrollBarSettings, **kwargs):
        self.bar_color, self.indicator_color, indicator_width = scrollbar_settings
        self.indicator_width = indicator_width >> 1
        self._grabbed = False

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        parent = self.parent
        h, w = parent.dim

        self.top = 0
        self.left = w - 2

        self.resize((h, 2))

        super().update_geometry()

    def render(self, canvas_view, colors_view, rect):
        indicator_width = self.indicator_width
        parent = self.parent
        fill_width = self.height - indicator_width - parent.show_horizontal_bar
        start_fill = round(parent.vertical_proportion * fill_width)

        self.colors[:, :, 3:] = self.bar_color
        self.colors[start_fill: start_fill + indicator_width, :, 3:] = self.indicator_color

        super().render(canvas_view, colors_view, rect)

    def on_click(self, mouse_event):
        if not (self.collides_coords(mouse_event.position) or self._grabbed):
            return super().on_click(mouse_event)

        if self._grabbed:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._grabbed = False
            else:
                dy = mouse_event.position[0] - self._last_y
                self._last_y = mouse_event.position[0]

                self.parent.vertical_proportion += dy / (self.height - self.indicator_width - self.parent.show_horizontal_bar)
        else:
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                self._grabbed =  True
                self._last_y = mouse_event.position[0]
            else:
                return super().on_click(mouse_event)

        return True


class HorizontalBar(Widget):
    def __init__(self, *args, scrollbar_settings: ScrollBarSettings, **kwargs):
        self.bar_color, self.indicator_color, self.indicator_width = scrollbar_settings
        self._grabbed = False

        super().__init__(*args, **kwargs)

    def update_geometry(self):
        parent = self.parent
        h, w = parent.dim

        self.top = h - 1
        self.left = 0

        self.resize((1, w - parent.show_vertical_bar * 2))

        super().update_geometry()

    def render(self, canvas_view, colors_view, rect):
        indicator_width = self.indicator_width
        fill_width = self.width - indicator_width
        start_fill = round(self.parent.horizontal_proportion * fill_width)

        self.colors[0, :, 3:] = self.bar_color
        self.colors[0, start_fill: start_fill + indicator_width, 3:] = self.indicator_color

        super().render(canvas_view, colors_view, rect)

    def on_click(self, mouse_event):
        if not (self.collides_coords(mouse_event.position) or self._grabbed):
            return super().on_click(mouse_event)

        if self._grabbed:
            if mouse_event.event_type == MouseEventType.MOUSE_UP:
                self._grabbed = False
            else:
                dx = mouse_event.position[1] - self._last_x
                self._last_x = mouse_event.position[1]

                self.parent.horizontal_proportion += dx / (self.width - self.indicator_width)
        else:
            if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
                self._grabbed =  True
                self._last_x = mouse_event.position[1]
            else:
                return super().on_click(mouse_event)

        return True
