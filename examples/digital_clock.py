import asyncio
import time
from itertools import chain

from nurses_2.app import App
from nurses_2.widgets.digital_display import DigitalDisplay, BRIGHT_GREEN_ON_BLACK
from nurses_2.widgets.text_widget import TextWidget

def _formatted_time(twelve_hour=False):
    hours, minutes, seconds = time.localtime()[3: 6]

    if twelve_hour:
        hours %= 12

    return chain.from_iterable(divmod(n, 10) for n in (hours, minutes, seconds))


class DigitalClock(TextWidget):
    def __init__(self, pos=(0, 0), twelve_hour=False, default_color_pair=BRIGHT_GREEN_ON_BLACK, **kwargs):
        super().__init__(
            size=(7, 47),
            pos=pos,
            default_color_pair=default_color_pair,
            **kwargs,
        )
        self.twelve_hour = twelve_hour

        offsets = (0, 0, 2, 2, 4, 4)
        for i in range(6):
            self.add_widget(DigitalDisplay(pos=(0, i * 7 + offsets[i])))

        self.canvas[[2, -3], 14] = self.canvas[[2, -3], 30] = "●"

        self._update_task = asyncio.create_task(self._update_time())

    async def _update_time(self):
        while True:
            for display, digit in zip(self.children, _formatted_time(self.twelve_hour)):
                display.show_digit(digit)

            await asyncio.sleep(1)


class DigitalClockApp(App):
    async def on_start(self):
        self.add_widget(DigitalClock(twelve_hour=True))


DigitalClockApp().run()
