from pathlib import Path

import numpy as np
from batgrl.app import App
from batgrl.gadgets.animation import Animation
from batgrl.gadgets.color_picker import ColorPicker
from batgrl.gadgets.file_chooser import FileChooser
from batgrl.gadgets.line_plot import LinePlot
from batgrl.gadgets.window import Window

ASSETS = Path(__file__).parent.parent / "assets"
CAVEMAN_PATH = ASSETS / "caveman"

XS = np.arange(20)

YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class WindowsApp(App):
    async def on_start(self):
        window_kwargs = dict(size=(25, 50), alpha=0.7)

        animation = Animation(path=CAVEMAN_PATH, interpolation="nearest")
        window_1 = Window(title=CAVEMAN_PATH.name, **window_kwargs)
        window_1.view = animation

        window_2 = Window(title="File Chooser", **window_kwargs)
        window_2.view = FileChooser(root_dir=ASSETS, alpha=0.5, is_transparent=True)

        window_3 = Window(title="Color Picker", **window_kwargs)
        window_3.view = ColorPicker(is_transparent=True, alpha=0.5)

        window_4 = Window(title="Line Plot", **window_kwargs)
        window_4.view = LinePlot(
            xs=[XS, XS, XS],
            ys=[YS_1, YS_2, YS_3],
            x_label="X Values",
            y_label="Y Values",
            legend_labels=("Before", "During", "After"),
            alpha=0.5,
            is_transparent=True,
        )

        self.add_gadgets(window_1, window_2, window_3, window_4)
        animation.play()


if __name__ == "__main__":
    WindowsApp(title="Windows Example").run()
