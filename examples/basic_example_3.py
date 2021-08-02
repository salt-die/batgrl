"""
Scatter and DraggableBehavior example.
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, WHITE, gradient, color_pair
from nurses_2.widgets import Widget
from nurses_2.widgets.scatter import Scatter
from nurses_2.widgets.behaviors import AutoSizeBehavior
from nurses_2.widgets.behaviors.draggable_behavior import DraggableBehavior

WHITE_ON_GREEN = color_pair(WHITE, GREEN)
WHITE_ON_BLUE = color_pair(WHITE, BLUE)


class BorderWidget(AutoSizeBehavior, DraggableBehavior, Widget):
    ...


class AutoGeometryScatter(Scatter):
    def __init__(self, **kwargs):
        super().__init__(pos=(1, 1), **kwargs)

    def update_geometry(self):
        h, w = self.parent.dim

        self.resize((h - 2, w - 2))

        super().update_geometry()


class PrettyWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.colors[:] = 50
        grad = gradient((self.width >> 1) - 1, WHITE_ON_GREEN, WHITE_ON_BLUE)
        self.colors[1:-1, 1:-1] = grad + grad[::-1]
        asyncio.create_task(self.roll())

    async def roll(self):
        while True:
            self.colors[1:-1, 1:-1] = np.roll(self.colors[1:-1, 1:-1], -1, (1, ))

            await asyncio.sleep(.11)


class MyApp(App):
    async def on_start(self):
        widget_1 = PrettyWidget(dim=(20, 40))
        widget_2 = PrettyWidget(dim=(10, 50))

        autogeometry_scatter = AutoGeometryScatter(default_color_pair=25)
        autogeometry_scatter.add_widgets(widget_1, widget_2)

        border_widget = BorderWidget(size_hint=(.75, .75), default_color_pair=WHITE_ON_BLUE)
        border_widget.add_widget(autogeometry_scatter)

        self.root.add_widget(border_widget)


MyApp().run()
