import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.line_plot import LinePlot

XS = np.arange(20)

YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)

run_widget_as_app(
    LinePlot(
        XS,
        YS_1,
        XS,
        YS_2,
        XS,
        YS_3,
        xlabel="X Values",
        ylabel="Y Values",
        legend_labels=("Before", "During", "After"),
        size_hint=(1.0, 1.0),
        background_color_pair=DEFAULT_COLOR_THEME.primary,
    )
)
