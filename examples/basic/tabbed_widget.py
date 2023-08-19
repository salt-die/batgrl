from pathlib import Path

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.animation import Animation, Interpolation
from nurses_2.widgets.color_picker import ColorPicker
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.line_plot import LinePlot
from nurses_2.widgets.tabbed_widget import TabbedWidget

import numpy as np

ASSETS = Path(__file__).parent.parent / "assets"
CAVEMAN_PATH = ASSETS / "caveman"
XS = np.arange(20)
YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class TabApp(App):
    async def on_start(self):
        tabbed = TabbedWidget(size_hint=(1.0, 1.0))

        animation = Animation(path=CAVEMAN_PATH, interpolation=Interpolation.NEAREST, size_hint=(1.0, 1.0))
        animation.play()
        tabbed.add_tab("Animation", animation)
        tabbed.add_tab("File Chooser", FileChooser(root_dir=ASSETS, size_hint=(1.0, 1.0)))
        tabbed.add_tab("Color Picker", ColorPicker(size_hint=(1.0, 1.0)))
        tabbed.add_tab(
            "Line Plot",
            LinePlot(
                XS, YS_1, XS, YS_2, XS, YS_3,
                xlabel="X Values",
                ylabel="Y Values",
                legend_labels=("Before", "During", "After"),
                background_color_pair=DEFAULT_COLOR_THEME.primary,
                size_hint=(1.0, 1.0),
            ),
        )
        self.add_widget(tabbed)

TabApp(title="Tabbed Widget").run()
