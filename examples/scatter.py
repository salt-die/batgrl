"""
ScatterBehavior, GrabMoveBehavior, and GrabResizeBehavior all inherit from GrabbableBehavior.
If you want all behaviors on a single widget, order of inheritance is important!
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, WHITE, gradient, ColorPair, AColor
from nurses_2.widgets.behaviors.grab_move_behavior import GrabMoveBehavior
from nurses_2.widgets.behaviors.grab_resize_behavior import GrabResizeBehavior
from nurses_2.widgets.behaviors.scatter_behavior import ScatterBehavior
from nurses_2.widgets.widget import Widget
from nurses_2.widgets.text_widget import TextWidget

WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)
WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)
DARK_GREY = ColorPair(25, 25, 25, 25, 25, 25)
GREY = AColor(50, 50, 50)


class Window(GrabResizeBehavior, ScatterBehavior, GrabMoveBehavior, Widget):
    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.pull_border_to_front()


class PrettyWidget(TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        grad = gradient(WHITE_ON_GREEN, WHITE_ON_BLUE, (self.width >> 1) - 2)

        self.colors[:] = 50
        self.colors[1:-1, 2:-2] = grad + grad[::-1]

        asyncio.create_task(self.roll())

    async def roll(self):
        while True:
            self.colors[1:-1, 2:-2] = np.roll(self.colors[1:-1, 2:-2], -1, (1, ))

            await asyncio.sleep(.11)


class MyApp(App):
    async def on_start(self):
        widget_1 = PrettyWidget(size=(20, 40))
        widget_2 = PrettyWidget(size=(10, 50))

        draggable_scatter = Window(size=(30, 100), background_color_pair=DARK_GREY, border_color=GREY)
        draggable_scatter.add_widgets(widget_1, widget_2)
        draggable_scatter.pull_border_to_front()

        self.add_widget(draggable_scatter)


MyApp(title="Scatter Example").run()
