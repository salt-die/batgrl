from ...colors import BLACK, color_pair
from ...mouse import MouseEventType
from ..widget import Widget
from .indicators import _VerticalIndicator, _HorizontalIndicator
from .scrollbar_data_structures import ScrollBarSettings

VBAR_WIDTH = 2
HBAR_HEIGHT = 1


class _VerticalBar(Widget):
    def __init__(self, settings: ScrollBarSettings, parent):
        bar_color, *indicator_settings = settings

        super().__init__(default_color_pair=color_pair(BLACK, bar_color))

        self.parent = parent
        self.update_geometry()

        self.indicator = _VerticalIndicator(*indicator_settings)
        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.left = w - VBAR_WIDTH
        self.resize((h, VBAR_WIDTH))

        super().update_geometry()

    @property
    def fill_width(self):
        return (
            self.height
            - self.indicator.height
            - self.parent.show_horizontal_bar * HBAR_HEIGHT
        )

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_coords(mouse_event.position)
        ):
            y = self.absolute_to_relative_coords(mouse_event.position).y
            sv = self.parent

            if y == self.height - HBAR_HEIGHT and sv.show_horizontal_bar:
                # Special case for the corner between the two scrollbars.
                return True

            sv.vertical_proportion = y / self.fill_width
            self.indicator.grab(mouse_event)
            return True


class _HorizontalBar(Widget):
    def __init__(self, settings: ScrollBarSettings, parent):
        bar_color, *indicator_settings = settings

        super().__init__(default_color_pair=color_pair(BLACK, bar_color))

        self.parent = parent
        self.update_geometry()

        self.indicator = _HorizontalIndicator(*indicator_settings)
        self.add_widget(self.indicator)

    def update_geometry(self):
        h, w = self.parent.dim

        self.top = h - HBAR_HEIGHT
        self.resize((HBAR_HEIGHT, w))

        super().update_geometry()

    @property
    def fill_width(self):
        return (
            self.width
            - self.indicator.width
            - self.parent.show_vertical_bar * VBAR_WIDTH
        )

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type == MouseEventType.MOUSE_DOWN
            and self.collides_coords(mouse_event.position)
        ):
            x = self.absolute_to_relative_coords(mouse_event.position).x
            sv = self.parent

            if x >= self.width - VBAR_WIDTH and sv.show_vertical_bar:
                # Special case for the corner between the two scrollbars.
                return True

            sv.horizontal_proportion = x / self.fill_width
            self.indicator.grab(mouse_event)
            return True
