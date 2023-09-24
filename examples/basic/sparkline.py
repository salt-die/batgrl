import numpy as np

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.button import Button
from nurses_2.widgets.sparkline import Sparkline

PRIMARY_COLOR = DEFAULT_COLOR_THEME.primary


class SparklineApp(App):
    async def on_start(self):
        sparkline_a = Sparkline(size=(4, 30), default_color_pair=PRIMARY_COLOR)
        sparkline_b = Sparkline(
            size=(4, 30), pos=(5, 0), default_color_pair=PRIMARY_COLOR
        )

        i = 0

        def new_data():
            nonlocal i
            sparkline_a.data = np.sin(np.linspace(i, 2 * np.pi + i, num=200))
            sparkline_b.data = np.random.random(200)
            i += 0.5

        new_data()

        button = Button(
            size=(9, 20),
            pos=(0, sparkline_a.right + 1),
            label="New Data",
            callback=new_data,
        )

        self.add_widgets(sparkline_a, sparkline_b, button)


if __name__ == "__main__":
    SparklineApp(title="Sparkline Example", background_color_pair=PRIMARY_COLOR).run()
