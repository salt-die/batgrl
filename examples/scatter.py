"""
ScatterBehavior, GrabMoveBehavior, and GrabResizeBehavior all inherit from GrabbableBehavior.
If you want all behaviors on a single widget, order of inheritance is important!
"""
import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import BLUE, GREEN, WHITE, gradient, ColorPair
from nurses_2.widgets.behaviors.grab_move_behavior import GrabMoveBehavior
from nurses_2.widgets.behaviors.grab_resize_behavior import GrabResizeBehavior
from nurses_2.widgets.behaviors.scatter_behavior import ScatterBehavior
from nurses_2.widgets.text_widget import TextWidget, Size

WHITE_ON_GREEN = ColorPair.from_colors(WHITE, GREEN)
WHITE_ON_BLUE = ColorPair.from_colors(WHITE, BLUE)
BLUE_ON_DARK_GREY = ColorPair(*BLUE, 25, 25, 25)
GREY_ON_GREY = ColorPair(50, 50, 50, 50, 50, 50)


class Window(GrabResizeBehavior, ScatterBehavior, GrabMoveBehavior, TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self._border_widget = TextWidget(default_color_pair=GREY_ON_GREY, is_transparent=True)
        self.resize(self.size)

    def resize(self, size: Size):
        super().resize(size)
        self._border_widget.resize(size)

        border_canvas = self._border_widget.canvas
        border_canvas[:] = " "
        border_canvas[[0, -1]] = border_canvas[:, [0, 1, -2, -1]] = "█"

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        super().render(canvas_view, colors_view, source)
        self._border_widget.render_intersection(source, canvas_view, colors_view)


class PrettyWidget(TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        grad = gradient(WHITE_ON_GREEN, WHITE_ON_BLUE, (self.width >> 1) - 2)

        self.colors[:] = GREY_ON_GREY
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

        draggable_scatter = Window(size=(30, 100), default_color_pair=BLUE_ON_DARK_GREY)
        draggable_scatter.add_widgets(widget_1, widget_2)

        self.add_widget(draggable_scatter)


MyApp().run()
