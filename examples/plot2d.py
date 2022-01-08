import numpy as np

from nurses_2.app import App
from nurses_2.colors import RED, BLUE, BLACK, ColorPair
from nurses_2.widgets.plot_2d import Plot2D

RED_ON_BLACK = ColorPair.from_colors(RED, BLACK)
BLUE_ON_BLACK = ColorPair.from_colors(BLUE, BLACK)

XS = np.arange(20)

YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)


class MyPlots(App):
    async def on_start(self):
        ymin = min(YS_1.min(), YS_2.min())
        ymax = max(YS_1.max(), YS_2.max())

        common_kwargs = dict(
            ymin=ymin,
            ymax=ymax,
            size_hint=(1.0, 1.0),
            is_transparent=True,
        )

        self.add_widgets(
            Plot2D(XS, YS_1, default_color_pair=RED_ON_BLACK, **common_kwargs),
            Plot2D(XS, YS_2, default_color_pair=BLUE_ON_BLACK, **common_kwargs),
        )


MyPlots().run()
