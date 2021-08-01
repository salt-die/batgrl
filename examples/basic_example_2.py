"""
ScrollView example.
"""
from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, RED, WHITE, gradient, color_pair
from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors import AutoPositionBehavior, Anchor
from nurses_2.widgets.scroll_view import ScrollView
from nurses_2.widgets.widget_data_structures import Size

N = 20  # Number of coordinate pairs on each line.
BIG_WIDGET_SIZE = Size(50, 8 * N + N - 1)

WHITE_ON_RED = color_pair(WHITE, RED)
WHITE_ON_GREEN = color_pair(WHITE, GREEN)
WHITE_ON_BLUE = color_pair(WHITE, BLUE)

LEFT_GRADIENT = gradient(BIG_WIDGET_SIZE.height, WHITE_ON_RED, WHITE_ON_GREEN)
RIGHT_GRADIENT = gradient(BIG_WIDGET_SIZE.height, WHITE_ON_GREEN, WHITE_ON_BLUE)


class AutoPositionScrollView(AutoPositionBehavior, ScrollView):
    pass


class MyApp(App):
    async def on_start(self):
        big_widget = Widget(dim=BIG_WIDGET_SIZE)

        for y in range(BIG_WIDGET_SIZE.height):
            big_widget.add_text(" ".join(f'({y:<2}, {x:<2})' for x in range(N)), row=y)
            big_widget.colors[y] = gradient(BIG_WIDGET_SIZE.width, LEFT_GRADIENT[y], RIGHT_GRADIENT[y])

        scroll_view = AutoPositionScrollView(dim=(10, 30), anchor=Anchor.CENTER, pos_hint=(0.5, 0.5))
        scroll_view.add_widget(big_widget)

        self.root.add_widget(scroll_view)


MyApp().run()
