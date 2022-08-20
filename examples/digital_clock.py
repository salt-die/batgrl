import asyncio
import time

from nurses_2.app import App
from nurses_2.widgets.digital_display import DigitalDisplay, BRIGHT_GREEN_ON_BLACK
from nurses_2.widgets.text_widget import TextWidget


class DigitalClock(TextWidget):
    def __init__(self, pos=(0, 0), twelve_hour=False, default_color_pair=BRIGHT_GREEN_ON_BLACK, **kwargs):
        super().__init__(
            size=(7, 52),
            pos=pos,
            default_color_pair=default_color_pair,
            **kwargs,
        )
        self.twelve_hour = twelve_hour

        for i in range(6):
            self.add_widget(DigitalDisplay(pos=(0, i * 8 + i // 2 * 2)))

        self.canvas[[2, -3], 16] = self.canvas[[2, -3], 34] = "●"

        self._update_task = asyncio.create_task(self._update_time())

    def _formatted_time(self):
        hours, minutes, seconds = time.localtime()[3: 6]

        if self.twelve_hour:
            hours %= 12

        for unit in (hours, minutes, seconds):
            for n in divmod(unit, 10):
                yield n

    async def _update_time(self):
        while True:
            for display, digit in zip(self.children, self._formatted_time()):
                display.show_char(str(digit))

            await asyncio.sleep(1)


class TestDisplay(DigitalDisplay):
    """
    Display any key pressed.
    """
    def on_keypress(self, key_press_event):
        key = key_press_event.key
        if isinstance(key, str) and len(key) == 1:
            self.show_char(key)

            return True


class DigitalClockApp(App):
    async def on_start(self):
        self.add_widgets(DigitalClock(twelve_hour=True), TestDisplay(pos=(10, 0)))


DigitalClockApp(title="Digital Clock Example").run()
