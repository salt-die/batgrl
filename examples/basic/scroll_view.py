"""
ScrollView example.
"""
from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, RED, WHITE, gradient, ColorPair
from nurses_2.widgets.text_widget import TextWidget, Anchor, Size
from nurses_2.widgets.scroll_view import ScrollView

N = 20  # Number of coordinate pairs on each line.
BIG_WIDGET_SIZE = Size(50, 8 * N + N - 1)

WHITE_ON_RED = ColorPair.from_colors(WHITE, RED)
WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)
WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)

LEFT_GRADIENT = gradient(WHITE_ON_RED, WHITE_ON_GREEN, BIG_WIDGET_SIZE.rows)
RIGHT_GRADIENT = gradient(WHITE_ON_GREEN, WHITE_ON_BLUE, BIG_WIDGET_SIZE.rows)



class MyApp(App):
    async def on_start(self):
        big_widget = TextWidget(size=BIG_WIDGET_SIZE)

        for y in range(BIG_WIDGET_SIZE.rows):
            big_widget.add_str(" ".join(f"({y:<2}, {x:<2})" for x in range(N)), (y, 0))
            big_widget.colors[y] = gradient(LEFT_GRADIENT[y], RIGHT_GRADIENT[y], BIG_WIDGET_SIZE.columns)

        scroll_view = ScrollView(size=(10, 30), anchor=Anchor.CENTER, pos_hint=(0.5, 0.5))
        scroll_view.view = big_widget

        self.add_widget(scroll_view)


MyApp(title="Scroll View Example").run()
