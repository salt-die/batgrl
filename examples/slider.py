"""
Example slider widget.
"""
import asyncio

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, BLACK, RED, WHITE, ColorPair
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.slider import Slider

GREEN_ON_BLACK = ColorPair.from_colors(GREEN, BLACK)
GREEN_ON_WHITE = ColorPair.from_colors(GREEN, WHITE)


class MyApp(App):
    async def on_start(self):
        display = TextWidget(size=(2, 30))
        display.add_text("Slider 1 Value:", row=0)
        display.add_text("Slider 2 Value:", row=1)

        slider_1 = Slider(
            size=(1, 20),
            pos=(2, 0),
            min=0,
            max=100,
            handle_color=BLUE,
            callback=lambda value: display.add_text(f"{round(value, 3):<10}", row=0, column=16),
            fill_color=RED,
            default_color_pair=GREEN_ON_BLACK,
        )
        slider_2 = Slider(
            size=(3, 15),
            pos=(3, 0),
            min=-20,
            max=50,
            handle_color=BLUE,
            callback=lambda value: display.add_text(f"{round(value, 3):<10}", row=1, column=16),
            fill_color=RED,
            default_color_pair=GREEN_ON_WHITE,
        )
        self.add_widgets(display, slider_1, slider_2)


MyApp(title="Slider Example").run()
