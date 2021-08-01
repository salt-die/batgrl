from ...colors import BLACK, color_pair
from ...mouse import MouseEventType
from ..widget import Widget
from .indicators import _VerticalIndicator, _HorizontalIndicator
from .scrollbar_data_structures import ScrollBarSettings


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
                # Special case for the corner between the two scrollbars.
                return True

            sv.vertical_proportion = y / self.fill_width
            self.indicator.update_geometry()
            self.indicator.grab(mouse_event)
            return True


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
                # Special case for the corner between the two scrollbars.
                return True

            sv.horizontal_proportion = x / self.fill_width
            self.indicator.update_geometry()
            self.indicator.grab(mouse_event)
            return True
