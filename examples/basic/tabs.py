from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.animation import Animation
from nurses_2.widgets.color_picker import ColorPicker
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.line_plot import LinePlot
from nurses_2.widgets.tabs import Tabs

ASSETS = Path(__file__).parent.parent / "assets"
CAVEMAN_PATH = ASSETS / "caveman"
XS = np.arange(20)
YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class TabApp(App):
    async def on_start(self):
        tabs = Tabs(size_hint={"height_hint": 1.0, "width_hint": 1.0})

        animation = Animation(
            path=CAVEMAN_PATH,
            interpolation="nearest",
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
        )
        animation.play()
        tabs.add_tab("Animation", animation)
        tabs.add_tab(
            "File Chooser",
            FileChooser(
                root_dir=ASSETS, size_hint={"height_hint": 1.0, "width_hint": 1.0}
            ),
        )
        tabs.add_tab(
            "Color Picker",
            ColorPicker(size_hint={"height_hint": 1.0, "width_hint": 1.0}),
        )
        tabs.add_tab(
            "Line Plot",
            LinePlot(
                xs=[XS, XS, XS],
                ys=[YS_1, YS_2, YS_3],
                x_label="X Values",
                y_label="Y Values",
                legend_labels=("Before", "During", "After"),
                plot_color_pair=DEFAULT_COLOR_THEME.primary,
                size_hint={"height_hint": 1.0, "width_hint": 1.0},
            ),
        )
        self.add_widget(tabs)


if __name__ == "__main__":
    TabApp(title="Tabbed Widget").run()
