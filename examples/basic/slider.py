"""
Example slider widget.
"""
from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.slider import Slider
from nurses_2.widgets.text_widget import TextWidget


class SliderApp(App):
    async def on_start(self):
        display = TextWidget(
            size=(3, 30), default_color_pair=DEFAULT_COLOR_THEME.primary
        )
        slider_1 = Slider(
            size=(1, 20),
            pos=(1, 0),
            min=0,
            max=100,
            callback=lambda value: display.add_str(f"{round(value, 3):<10}", (0, 7)),
        )
        slider_2 = Slider(
            size=(3, 16),
            pos=(3, 2),
            min=-20,
            max=50,
            callback=lambda value: display.add_str(f"{round(value, 3):<10}", (2, 7)),
            fill_color=(220, 120, 0),
            default_color_pair=DEFAULT_COLOR_THEME.button_normal,
        )
        self.add_widgets(display, slider_1, slider_2)


if __name__ == "__main__":
    SliderApp(
        title="Slider Example", background_color_pair=DEFAULT_COLOR_THEME.primary
    ).run()
