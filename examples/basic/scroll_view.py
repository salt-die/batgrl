"""ScrollView example."""
from batgrl.app import App
from batgrl.colors import BLUE, GREEN, RED, gradient
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Size, Text

N = 20  # Number of coordinate pairs on each line.
BIG_GADGET_SIZE = Size(50, 8 * N + N - 1)

LEFT_GRADIENT = gradient(RED, GREEN, BIG_GADGET_SIZE.rows)
RIGHT_GRADIENT = gradient(GREEN, BLUE, BIG_GADGET_SIZE.rows)


class ScrollViewApp(App):
    async def on_start(self):
        big_gadget = Text(size=BIG_GADGET_SIZE)

        for y in range(BIG_GADGET_SIZE.rows):
            big_gadget.add_str(
                " ".join(f"({y:<2}, {x:<2})" for x in range(N)), pos=(y, 0)
            )
            big_gadget.canvas["bg_color"][y] = gradient(
                LEFT_GRADIENT[y], RIGHT_GRADIENT[y], BIG_GADGET_SIZE.columns
            )

        scroll_view = ScrollView(size=(20, 50), pos_hint={"y_hint": 0.5, "x_hint": 0.5})
        scroll_view.view = big_gadget

        self.add_gadget(scroll_view)


if __name__ == "__main__":
    ScrollViewApp(title="Scroll View Example").run()
