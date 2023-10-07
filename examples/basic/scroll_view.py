"""
ScrollView example.
"""
from batgrl.app import App
from batgrl.colors import BLUE, GREEN, RED, WHITE, ColorPair, gradient
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Size, Text

N = 20  # Number of coordinate pairs on each line.
BIG_WIDGET_SIZE = Size(50, 8 * N + N - 1)

WHITE_ON_RED = ColorPair.from_colors(WHITE, RED)
WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)
WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)

LEFT_GRADIENT = gradient(WHITE_ON_RED, WHITE_ON_GREEN, BIG_WIDGET_SIZE.rows)
RIGHT_GRADIENT = gradient(WHITE_ON_GREEN, WHITE_ON_BLUE, BIG_WIDGET_SIZE.rows)


class ScrollViewApp(App):
    async def on_start(self):
        big_gadget = Text(size=BIG_WIDGET_SIZE)

        for y in range(BIG_WIDGET_SIZE.rows):
            big_gadget.add_str(" ".join(f"({y:<2}, {x:<2})" for x in range(N)), (y, 0))
            big_gadget.colors[y] = gradient(
                LEFT_GRADIENT[y], RIGHT_GRADIENT[y], BIG_WIDGET_SIZE.columns
            )

        scroll_view = ScrollView(size=(10, 30), pos_hint={"y_hint": 0.5, "x_hint": 0.5})
        scroll_view.view = big_gadget

        self.add_gadget(scroll_view)


if __name__ == "__main__":
    ScrollViewApp(title="Scroll View Example").run()
