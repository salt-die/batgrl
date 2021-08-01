from typing import NamedTuple

from ...colors import BLACK, Color, color_pair
from ...mouse import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


class ScrollBarSettings(NamedTuple):
    """
    Settings for ScrollView scrollbars. `indicator_length`
    is doubled for horizontal scrollbars.
    """
    bar_color: Color
    indicator_inactive_color: Color
    indicator_hover_color: Color
    indicator_active_color: Color
    indicator_length: int  # This value doubled for horizontal scrollbars.


class _IndicatorBehavior:
    """
    Common behavior for vertical and horizontal indicators.
    """
    def update_color(self, mouse_event):
        if self.collides_coords(mouse_event.position):
            self.colors[..., 3:] = self.hover_color
        else:
            self.colors[..., 3:] = self.inactive_color

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self.update_color(mouse_event)

    def on_click(self, mouse_event):
        if (
            not super().on_click(mouse_event)
            and mouse_event.event_type == MouseEventType.MOUSE_MOVE
        ):
            self.update_color(mouse_event)


class _VerticalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self, inactive_color, hover_color, active_color, length):
        super().__init__(dim=(length, 2), default_color_pair=color_pair(BLACK, inactive_color))
        self.active_color = active_color
        self.hover_color = hover_color
        self.inactive_color = inactive_color

    def update_geometry(self):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent

        if scroll_view is None:
            return

        self.top = round(scroll_view.vertical_proportion * vertical_bar.fill_width)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.colors[..., 3:] = self.active_color
        self._last_y = mouse_event.position[0]

    def grab_update(self, mouse_event):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent

        dy = mouse_event.position[0] - self._last_y
        self._last_y = mouse_event.position[0]

        scroll_view.vertical_proportion += dy / vertical_bar.fill_width

        self.update_geometry()


class _VerticalBar(Widget):
    def __init__(self, settings: ScrollBarSettings):
        bar_color, *indicator_settings = settings

        super().__init__(default_color_pair=color_pair(BLACK, bar_color))

        self.indicator = _VerticalIndicator(*indicator_settings)
        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.left = w - 2
        self.resize((h, 2))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.height - self.indicator.height - self.parent.show_horizontal_bar

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_coords(mouse_event.position)
        ):
            y, _ = self.absolute_to_relative_coords(mouse_event.position)
            sv = self.parent

            if y == self.height - 1 and sv.show_horizontal_bar:
                return True

            sv.vertical_proportion = y / self.fill_width
            self.indicator.update_geometry()
            self.indicator.grab(mouse_event)
            return True


class _HorizontalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self, inactive_color, hover_color, active_color, length):
        super().__init__(dim=(1, length << 1), default_color_pair=color_pair(BLACK, inactive_color))
        self.active_color = active_color
        self.hover_color = hover_color
        self.inactive_color = inactive_color

    def update_geometry(self):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent

        if scroll_view is None:
            return

        self.left = round(scroll_view.horizontal_proportion * horizontal_bar.fill_width)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.colors[..., 3:] = self.active_color
        self._last_x = mouse_event.position[1]

    def grab_update(self, mouse_event):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent

        dx = mouse_event.position[1] - self._last_x
        self._last_x = mouse_event.position[1]

        scroll_view.horizontal_proportion += dx / horizontal_bar.fill_width

        self.update_geometry()


class _HorizontalBar(Widget):
    def __init__(self, settings: ScrollBarSettings):
        bar_color, *indicator_settings = settings

        super().__init__(default_color_pair=color_pair(BLACK, bar_color))
        self.indicator = _HorizontalIndicator(*indicator_settings)
        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.top = h - 1
        self.resize((1, w))

        super().update_geometry()

    @property
    def fill_width(self):
        return self.width - self.indicator.width - self.parent.show_vertical_bar * 2

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_coords(mouse_event.position)
        ):
            _, x = self.absolute_to_relative_coords(mouse_event.position)
            sv = self.parent

            if x >= self.width - 2 and sv.show_vertical_bar:
                return True

            sv.horizontal_proportion = x / self.fill_width
            self.indicator.update_geometry()
            self.indicator.grab(mouse_event)
            return True
