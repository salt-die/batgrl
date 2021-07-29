import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import ColorPair, gradient, BLUE, WHITE, YELLOW
from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors import ButtonBehavior

WHITE_ON_BLUE = ColorPair(*WHITE, *BLUE)
WHITE_ON_YELLOW = ColorPair(*WHITE, *YELLOW)

class MyButton(ButtonBehavior, Widget):
    GRADIENT = (
        gradient(10, WHITE_ON_YELLOW, WHITE_ON_BLUE)
        + gradient(10, WHITE_ON_BLUE, WHITE_ON_YELLOW)
    )

    def __init__(self, info_display, **kwargs):
        self.info_display = info_display
        self._down_roll_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

        super().__init__(dim=(5, 20), **kwargs)

        self.add_text(f"{'Press Me':^{self.width}}", row=self.height // 2)

    def update_down(self):
        self.colors[:, :] = self.GRADIENT

        self._down_roll_task = asyncio.create_task(self._down_roll())

    async def _down_roll(self):
        while True:
            self.colors = np.roll(self.colors, 1, axis=(1, ))

            try:
                await asyncio.sleep(.1)
            except asyncio.CancelledError:
                return

    def update_normal(self):
        self._down_roll_task.cancel()
        self.colors[:, :] = WHITE_ON_BLUE

    def on_release(self):
        self.info_display.add_text(f"{'Pressed!':<8}", row=0, column=19)
        asyncio.create_task(self._reset_view())

    def on_click(self, mouse_event):
        info = self.info_display
        info.add_text(f"{str(mouse_event.position):<17}", row=1, column=10)
        info.add_text(f"{str(mouse_event.event_type)[15:35]:<20}", row=2, column=7)
        info.add_text(f"{str(mouse_event.button)[12:]:<19}", row=3, column=8)
        info.add_text(f"{str(mouse_event.modifier)[14:]:<17}"[:17], row=4, column=10)
        return super().on_click(mouse_event)

    async def _reset_view(self):
        await asyncio.sleep(2)
        self.info_display.canvas[0, 18:] = " "


class MyApp(App):
    async def on_start(self):
        info_display = Widget(dim=(5, 27))
        info_display.add_text("Waiting for input:", row=0)
        info_display.add_text("Position:", row=1)
        info_display.add_text("Event:", row=2)
        info_display.add_text("Button:", row=3)
        info_display.add_text("Modifier:", row=4)

        button = MyButton(info_display, pos=(10, 10))

        self.root.add_widgets(button, info_display)


MyApp().run()
