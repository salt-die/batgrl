from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.colors import Color, ColorPair
from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.color_picker import ColorPicker
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.line_plot import LinePlot
from nurses_2.widgets.window import Window

THIS_DIR = Path(__file__).parent
CAVEMAN_PATH = THIS_DIR / "frames" / "caveman"

LIGHT_BLUE = Color.from_hex("56a1e2")
DARK_PURPLE = Color.from_hex("020028")

XS = np.arange(20)

YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class MyApp(App):
    async def on_start(self):
        animation = Animation(size_hint=(1.0, 1.0), path=CAVEMAN_PATH, interpolation=Interpolation.NEAREST)
        animation.play()
        window_1 = Window(size=(25, 50), alpha=.7, title=CAVEMAN_PATH.name)
        window_1.add_widget(animation)

        window_2 = Window(size=(25, 50), alpha=.7, title="File Chooser")
        window_2.add_widget(FileChooser(size_hint=(1.0, 1.0)))

        window_3 = Window(size=(25, 50), alpha=.7, title="Color Picker")
        window_3.add_widget(ColorPicker(size_hint=(1.0, 1.0)))

        window_4 = Window(size=(25, 50), alpha=.7, title="Line Plot")
        window_4.add_widget(
            LinePlot(
                XS, YS_1, XS, YS_2, XS, YS_3,
                xlabel="X Values",
                ylabel="Y Values",
                legend_labels=("Before", "During", "After"),
                size_hint=(1.0, 1.0),
                background_color_pair=ColorPair.from_colors(LIGHT_BLUE, DARK_PURPLE),
            )
        )

        self.add_widgets(window_1, window_2, window_3, window_4)


MyApp(title="Windows Example").run()
