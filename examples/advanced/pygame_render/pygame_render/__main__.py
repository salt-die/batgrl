from types import SimpleNamespace

import numpy as np

from batgrl.app import App
from batgrl.colors import DEFAULT_COLOR_THEME
from batgrl.gadgets.button import Button
from batgrl.gadgets.sparkline import Sparkline

from .pygame_input import PygameInput
from .pygame_output import PygameOutput


class PygameApp(App):
    def _create_io(self) -> tuple[SimpleNamespace, PygameOutput]:
        return PygameInput, PygameOutput()


# From examples/basic/sparkline.py
class SparklineApp(PygameApp):
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
    SparklineApp(
        title="Sparkline Example", background_color_pair=DEFAULT_COLOR_THEME.primary
    ).run()
