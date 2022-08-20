"""
Indicators for scroll view scrollbars.
"""
from ...io import MouseEventType
from ..behaviors.grabbable_behavior import GrabbableBehavior
from ..behaviors.themable import Themable
from ..widget import Widget


class _IndicatorBehavior(Themable):
    """
    Common behavior for vertical and horizontal indicators.
    """
    def update_theme(self):
        ct = self.color_theme
        self.inactive_color_pair = ct.primary_light_color_pair
        self.hover_color_pair = ct.primary_color_pair
        self.active_color_pair = ct.secondary_color_pair

        if not self.parent:
            self.background_color_pair = self.inactive_color_pair
        elif self.is_grabbed:
            self.background_color_pair = self.active_color_pair
        elif self.collides_point(self._last_mouse_pos):
            self.background_color_pair = self.hover_color_pair
        else:
            self.background_color_pair = self.inactive_color_pair

    def update_color(self, mouse_event):
        if self.collides_point(mouse_event.position):
            self.background_color_pair = self.hover_color_pair
        else:
            self.background_color_pair = self.inactive_color_pair

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.background_color_pair = self.active_color_pair

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self.update_color(mouse_event)

    def on_mouse(self, mouse_event):
        if super().on_mouse(mouse_event):
            return True

        if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            self.update_color(mouse_event)


class _VerticalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self):
        super().__init__(size=(2, 2))
        self.update_theme()

    def update_geometry(self):
        if (vertical_bar := self.parent) and (scroll_view := vertical_bar.parent):
            self.top = round(scroll_view.vertical_proportion * vertical_bar.fill_height)

    def grab_update(self, mouse_event):
        vertical_bar = self.parent
        scroll_view = vertical_bar.parent
        scroll_view.vertical_proportion += self.mouse_dy / vertical_bar.fill_height


class _HorizontalIndicator(_IndicatorBehavior, GrabbableBehavior, Widget):
    def __init__(self):
        super().__init__(size=(1, 4))
        self.update_theme()

    def update_geometry(self):
        if (horizontal_bar := self.parent) and (scroll_view := horizontal_bar.parent):
            self.left = round(scroll_view.horizontal_proportion * horizontal_bar.fill_width)

    def grab_update(self, mouse_event):
        horizontal_bar = self.parent
        scroll_view = horizontal_bar.parent
        scroll_view.horizontal_proportion += self.mouse_dx / horizontal_bar.fill_width
