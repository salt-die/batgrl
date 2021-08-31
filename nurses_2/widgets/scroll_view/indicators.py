from ...colors import BLACK, color_pair
from ...io import MouseEventType
from ...widgets.behaviors.grabbable_behavior import GrabbableBehavior
from ..widget import Widget


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
        if super().on_click(mouse_event):
            return True

        if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            self.update_color(mouse_event)


class _VerticalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self, inactive_color, hover_color, active_color, length):
        super().__init__(size=(length, 2), default_color_pair=color_pair(BLACK, inactive_color))
        self.active_color = active_color
        self.hover_color = hover_color
        self.inactive_color = inactive_color

    def update_geometry(self):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent

        self.top = round(scroll_view.vertical_proportion * vertical_bar.fill_height)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.colors[..., 3:] = self.active_color

    def grab_update(self, mouse_event):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent

        scroll_view.vertical_proportion += self.mouse_dy / vertical_bar.fill_height


class _HorizontalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self, inactive_color, hover_color, active_color, length):
        super().__init__(size=(1, length << 1), default_color_pair=color_pair(BLACK, inactive_color))
        self.active_color = active_color
        self.hover_color = hover_color
        self.inactive_color = inactive_color

    def update_geometry(self):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent

        self.left = round(scroll_view.horizontal_proportion * horizontal_bar.fill_width)

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.colors[..., 3:] = self.active_color

    def grab_update(self, mouse_event):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent

        scroll_view.horizontal_proportion += self.mouse_dx / horizontal_bar.fill_width
