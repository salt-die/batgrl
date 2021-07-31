from nurses_2.app import App
from nurses_2.colors import BLUE, BLACK, RED, WHITE, gradient, color_pair
from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors import AutoPositionBehavior, Anchor
from nurses_2.widgets.scroll_view import ScrollView
from nurses_2.widgets.widget_data_structures import Size

N = 20
BIG_WIDGET_SIZE = Size(50, 8 * N + N - 1)

WHITE_ON_BLUE = color_pair(WHITE, BLUE)
WHITE_ON_RED = color_pair(WHITE, RED)
BLACK_ON_BLUE = color_pair(BLACK, BLUE)
BLACK_ON_RED = color_pair(BLACK, RED)

LEFT_GRADIENT = gradient(BIG_WIDGET_SIZE.height, WHITE_ON_BLUE, BLACK_ON_BLUE)
RIGHT_GRADIENT = gradient(BIG_WIDGET_SIZE.height, WHITE_ON_RED, BLACK_ON_RED)


class AutoPositionScrollView(AutoPositionBehavior, ScrollView):
    pass

class MyApp(App):
    async def on_start(self):
        big_widget = Widget(dim=BIG_WIDGET_SIZE)

        for i in range(BIG_WIDGET_SIZE.height):
            big_widget.add_text(" ".join(f'({i:<2}, {x:<2})' for x in range(N)), row=i)
            big_widget.colors[i] = gradient(BIG_WIDGET_SIZE.width, LEFT_GRADIENT[i], RIGHT_GRADIENT[i])

        scroll_view = AutoPositionScrollView(dim=(10, 30), anchor=Anchor.CENTER, pos_hint=(0.5, 0.5))
        scroll_view.add_widget(big_widget)

        self.root.add_widget(scroll_view)


MyApp().run()
