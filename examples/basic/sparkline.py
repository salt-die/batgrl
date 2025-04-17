import numpy as np
from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG
from batgrl.gadgets.button import Button
from batgrl.gadgets.sparkline import Sparkline


class SparklineApp(App):
    async def on_start(self):
        sparkline_a = Sparkline(size=(4, 30))
        sparkline_b = Sparkline(size=(4, 30), pos=(5, 0))

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

        self.add_gadgets(sparkline_a, sparkline_b, button)


if __name__ == "__main__":
    SparklineApp(title="Sparkline Example", bg_color=NEPTUNE_PRIMARY_BG).run()
