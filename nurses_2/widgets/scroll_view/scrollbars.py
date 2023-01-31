"""
Scrollbars for a scroll view.
"""
from ...io import MouseEventType
from ..widget import Widget
from ..behaviors.themable import Themable
from .indicators import _VerticalIndicator, _HorizontalIndicator


class _VerticalBar(Themable, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicator = _VerticalIndicator()
        self.add_widget(self.indicator)
        self.background_char = " "

    def update_theme(self):
        self.background_color_pair = self.color_theme.scrollbar * 2

    def on_add(self):
        super().on_add()

        def update_size_pos():
            h, w = self.parent.size
            self.x = w - 2
            self.height = h

        update_size_pos()
        self.subscribe(self.parent, "size", update_size_pos)

    def on_remove(self):
        self.unsubscribe(self.parent, "size")
        super().on_remove()

    @property
    def fill_height(self):
        """
        Height of the scroll bar minus the height of the indicator.
        """
        return (
            self.height
            - self.indicator.height
            - self.parent.show_horizontal_bar
        )

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.fill_height != 0
            and self.collides_point(mouse_event.position)
        ):
            y = self.to_local(mouse_event.position).y
            sv = self.parent

            if not sv.show_horizontal_bar or y < self.height - 1:
                sv.vertical_proportion = y / self.fill_height
                self.indicator.grab(mouse_event)

            return True


class _HorizontalBar(Themable, Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicator = _HorizontalIndicator()
        self.add_widget(self.indicator)
        self.background_char = " "

    def update_theme(self):
        self.background_color_pair = self.color_theme.scrollbar * 2

    def on_add(self):
        super().on_add()

        def update_size_pos():
            h, w = self.parent.size
            self.y = h - 1
            self.width = w

        update_size_pos()
        self.subscribe(self.parent, "size", update_size_pos)

    def on_remove(self):
        self.unsubscribe(self.parent, "size")
        super().on_remove()

    @property
    def fill_width(self):
        """
        Width of the scroll bar minus the width of the indicator.
        """
        return (
            self.width
            - self.indicator.width
            - self.parent.show_vertical_bar * 2
        )

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.fill_width != 0
            and self.collides_point(mouse_event.position)
        ):
            x = self.to_local(mouse_event.position).x
            sv = self.parent

            if not sv.show_vertical_bar or x < self.width - 2:
                sv.horizontal_proportion = x / self.fill_width
                self.indicator.grab(mouse_event)

            return True
