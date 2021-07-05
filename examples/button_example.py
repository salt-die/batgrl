import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import ColorPair, gradient, BLUE, WHITE, YELLOW
from nurses_2.widgets import Widget
from nurses_2.widgets.button_behavior import ButtonBehavior

WHITE_ON_BLUE = ColorPair(*WHITE, *BLUE)
WHITE_ON_YELLOW = ColorPair(*WHITE, *YELLOW)

class MyButton(ButtonBehavior, Widget):
    GRADIENT = (
        gradient(10, WHITE_ON_YELLOW, WHITE_ON_BLUE)
        + gradient(10, WHITE_ON_BLUE, WHITE_ON_YELLOW)
    )

    def __init__(self, output_view, event_view, pos=(0, 0), **kwargs):
        self.output_view = output_view
        self.event_view = event_view
        self._down_roll_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

        super().__init__(dim=(5, 20), pos=pos, **kwargs)

        self.add_text(f"{'Press Me':^20}", row=2)

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
        self.output_view.add_text('Pressed!')
        asyncio.create_task(self._reset_view())

    def on_click(self, mouse_event):
        self.event_view.add_text(f"{str(mouse_event.event_type)[15:35]:<20}")
        return super().on_click(mouse_event)

    async def _reset_view(self):
        await asyncio.sleep(2)
        self.output_view[:] = " "


class MyApp(App):
    async def on_start(self):
        info_display = Widget(dim=(2, 27))
        info_display.add_text("Waiting for input:", row=0)
        info_display.add_text("Event:", row=1)

        button = MyButton(info_display.get_view[0, 19:], info_display.get_view[1, 7:], pos=(10, 10))

        self.root.add_widgets(button, info_display)


MyApp().run()
