from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.animation import Animation
from nurses_2.widgets.color_picker import ColorPicker
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.line_plot import LinePlot
from nurses_2.widgets.window import Window

ASSETS = Path(__file__).parent.parent / "assets"
CAVEMAN_PATH = ASSETS / "caveman"

XS = np.arange(20)

YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class MyApp(App):
    async def on_start(self):
        window_kwargs = dict(size=(25, 50), border_alpha=0.7, alpha=0.7)

        animation = Animation(path=CAVEMAN_PATH, interpolation="nearest")
        window_1 = Window(title=CAVEMAN_PATH.name, **window_kwargs)
        window_1.view = animation

        window_2 = Window(title="File Chooser", **window_kwargs)
        window_2.view = FileChooser(root_dir=ASSETS)

        window_3 = Window(title="Color Picker", **window_kwargs)
        window_3.view = ColorPicker()

        window_4 = Window(title="Line Plot", **window_kwargs)
        window_4.view = LinePlot(
            xs=[XS, XS, XS],
            ys=[YS_1, YS_2, YS_3],
            x_label="X Values",
            y_label="Y Values",
            legend_labels=("Before", "During", "After"),
            plot_color_pair=DEFAULT_COLOR_THEME.primary,
        )

        self.add_widgets(window_1, window_2, window_3, window_4)
        animation.play()


MyApp(title="Windows Example").run()
