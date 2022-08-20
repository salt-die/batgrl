"""
Scrollbars for a scroll view.
"""
from ...io import MouseEventType
from ..widget import Widget
from ..behaviors.themable import Themable
from .indicators import _VerticalIndicator, _HorizontalIndicator

VBAR_WIDTH = 2
HBAR_HEIGHT = 1


class _VerticalBar(Themable, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.indicator = _VerticalIndicator()
        self.add_widget(self.indicator)
        self.background_char = " "
        self.update_theme()

    def update_theme(self):
        self.background_color_pair = self.color_theme.primary_dark_color_pair

    def update_geometry(self):
        h, w = self.parent.size

        self.left = w - VBAR_WIDTH
        self.size = h, VBAR_WIDTH

        super().update_geometry()

    @property
    def fill_height(self):
        """
        Height of the scroll bar minus the height of the indicator.
        """
        return (
            self.height
            - self.indicator.height
            - self.parent.show_horizontal_bar * HBAR_HEIGHT
        )

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_point(mouse_event.position)
        ):
            y = self.to_local(mouse_event.position).y
            sv = self.parent

            if not (y >= self.height - HBAR_HEIGHT and sv.show_horizontal_bar):
                sv.vertical_proportion = y / self.fill_height
                self.indicator.grab(mouse_event)

            return True


class _HorizontalBar(Themable, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.indicator = _HorizontalIndicator()
        self.add_widget(self.indicator)
        self.background_char = " "
        self.update_theme()

    def update_theme(self):
        self.background_color_pair = self.color_theme.primary_dark_color_pair

    def update_geometry(self):
        h, w = self.parent.size

        self.top = h - HBAR_HEIGHT
        self.size = HBAR_HEIGHT, w

        super().update_geometry()

    @property
    def fill_width(self):
        """
        Width of the scroll bar minus the width of the indicator.
        """
        return (
            self.width
            - self.indicator.width
            - self.parent.show_vertical_bar * VBAR_WIDTH
        )

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_point(mouse_event.position)
        ):
            x = self.to_local(mouse_event.position).x
            sv = self.parent

            if not (x >= self.width - VBAR_WIDTH and sv.show_vertical_bar):
                sv.horizontal_proportion = x / self.fill_width
                self.indicator.grab(mouse_event)

            return True
