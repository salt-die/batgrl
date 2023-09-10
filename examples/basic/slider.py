"""
Example slider widget.
"""
from nurses_2.app import App
from nurses_2.colors import BLACK, BLUE, GREEN, RED, WHITE, ColorPair
from nurses_2.widgets.slider import Slider
from nurses_2.widgets.text_widget import TextWidget

GREEN_ON_BLACK = ColorPair.from_colors(GREEN, BLACK)
GREEN_ON_WHITE = ColorPair.from_colors(GREEN, WHITE)
BLUE_ON_BLACK = ColorPair.from_colors(BLUE, BLACK)
BLUE_ON_WHITE = ColorPair.from_colors(BLUE, WHITE)


class MyApp(App):
    async def on_start(self):
        display = TextWidget(size=(2, 30))
        display.add_str("Slider 1 Value:")
        display.add_str("Slider 2 Value:", (1, 0))

        slider_1 = Slider(
            size=(1, 20),
            pos=(2, 0),
            min=0,
            max=100,
            handle_color_pair=BLUE_ON_BLACK,
            callback=lambda value: display.add_str(f"{round(value, 3):<10}", (0, 16)),
            fill_color=RED,
            default_color_pair=GREEN_ON_BLACK,
        )
        slider_2 = Slider(
            size=(3, 15),
            pos=(3, 0),
            min=-20,
            max=50,
            handle_color_pair=BLUE_ON_WHITE,
            callback=lambda value: display.add_str(f"{round(value, 3):<10}", (1, 16)),
            fill_color=RED,
            default_color_pair=GREEN_ON_WHITE,
        )
        self.add_widgets(display, slider_1, slider_2)


MyApp(title="Slider Example").run()
