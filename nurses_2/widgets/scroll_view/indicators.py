"""
Indicators for scroll view scrollbars.
"""
from ...io import MouseEventType
from ...clamp import clamp
from ..behaviors.grabbable_behavior import GrabbableBehavior
from ..behaviors.themable import Themable
from ..widget import Widget


class _IndicatorBehaviorBase(Themable, GrabbableBehavior, Widget):
    """
    Common behavior for vertical and horizontal indicators.
    """
    def __init__(self):
        super().__init__(size=(1, 2))

    def update_theme(self):
        self.background_color_pair = self.color_theme.scrollbar_indicator_normal * 2

    def update_color(self, mouse_event):
        if self.is_grabbed:
            self.background_color_pair = self.color_theme.scrollbar_indicator_press * 2
        elif self.collides_point(mouse_event.position):
            self.background_color_pair = self.color_theme.scrollbar_indicator_hover * 2
        else:
            self.background_color_pair = self.color_theme.scrollbar_indicator_normal * 2

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.update_color(mouse_event)

    def ungrab(self, mouse_event):
        super().ungrab(mouse_event)
        self.update_color(mouse_event)

    def on_mouse(self, mouse_event):
        if super().on_mouse(mouse_event):
            return True

        if mouse_event.event_type == MouseEventType.MOUSE_MOVE:
            self.update_color(mouse_event)


class _VerticalIndicator(_IndicatorBehaviorBase):
    def update_size_pos(self):
        bar = self.parent
        scroll_view = bar.parent
        if scroll_view.view == None:
            view_height = 1
        else:
            view_height = scroll_view.view.height

        self.height = clamp(int(scroll_view.port_height ** 2 / view_height), 1, scroll_view.port_height)
        self.y = round(scroll_view.vertical_proportion * bar.fill_height)

    def on_add(self):
        super().on_add()
        scroll_view = self.parent.parent
        self.update_size_pos()
        self.subscribe(scroll_view, "size", self.update_size_pos)
        self.subscribe(scroll_view, "vertical_proportion", self.update_size_pos)
        self.subscribe(scroll_view, "show_horizontal_bar", self.update_size_pos)

    def on_remove(self):
        scroll_view = self.parent.parent
        self.unsubscribe(scroll_view, "size")
        self.unsubscribe(scroll_view, "vertical_proportion")
        self.unsubscribe(scroll_view, "show_horizontal_bar")
        super().on_remove()

    def grab_update(self, mouse_event):
        bar = self.parent
        scroll_view = bar.parent
        if bar.fill_height == 0:
            scroll_view.vertical_proportion = 0
        else:
            scroll_view.vertical_proportion += self.mouse_dy / bar.fill_height


class _HorizontalIndicator(_IndicatorBehaviorBase):
    def update_size_pos(self):
        bar = self.parent
        scroll_view = bar.parent
        if scroll_view.view == None:
            view_width = 1
        else:
            view_width = scroll_view.view.width

        self.width = clamp(int(scroll_view.port_width ** 2 / view_width), 2, scroll_view.port_width)
        self.x = round(scroll_view.horizontal_proportion * bar.fill_width)

    def on_add(self):
        super().on_add()
        scroll_view = self.parent.parent
        self.update_size_pos()
        self.subscribe(scroll_view, "size", self.update_size_pos)
        self.subscribe(scroll_view, "horizontal_proportion", self.update_size_pos)
        self.subscribe(scroll_view, "show_vertical_bar", self.update_size_pos)

    def on_remove(self):
        scroll_view = self.parent.parent
        self.unsubscribe(scroll_view, "size")
        self.unsubscribe(scroll_view, "horizontal_proportion")
        self.unsubscribe(scroll_view, "show_vertical_bar")
        super().on_remove()

    def grab_update(self, mouse_event):
        bar = self.parent
        scroll_view = bar.parent
        if bar.fill_width == 0:
            scroll_view.horizontal_proportion = 0
        else:
            scroll_view.horizontal_proportion += self.mouse_dx / bar.fill_width
