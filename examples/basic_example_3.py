"""
Scatter and DraggableBehavior both inherit from GrabbableBehavior, but what
happens if you want a draggable Scatter? Exactly what you'd expect!
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, WHITE, gradient, color_pair
from nurses_2.widgets import Widget
from nurses_2.widgets.scatter import Scatter
from nurses_2.widgets.behaviors.draggable_behavior import DraggableBehavior

WHITE_ON_GREEN = color_pair(WHITE, GREEN)
WHITE_ON_BLUE = color_pair(WHITE, BLUE)


class DraggableScatter(DraggableBehavior, Scatter):
    ...


class PrettyWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        grad = gradient((self.width >> 1) - 2, WHITE_ON_GREEN, WHITE_ON_BLUE)

        self.colors[:] = 50
        self.colors[1:-1, 2:-2] = grad + grad[::-1]

        asyncio.create_task(self.roll())

    async def roll(self):
        while True:
            self.colors[1:-1, 2:-2] = np.roll(self.colors[1:-1, 2:-2], -1, (1, ))

            await asyncio.sleep(.11)


class MyApp(App):
    async def on_start(self):
        widget_1 = PrettyWidget(dim=(20, 40))
        widget_2 = PrettyWidget(dim=(10, 50))

        draggable_scatter = DraggableScatter(dim=(30, 100), default_color_pair=25)
        draggable_scatter.add_widgets(widget_1, widget_2)

        self.root.add_widget(draggable_scatter)


MyApp().run()
