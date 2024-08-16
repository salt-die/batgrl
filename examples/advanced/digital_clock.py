import asyncio
import time

from batgrl.app import App
from batgrl.gadgets.digital_display import BRIGHT_GREEN, DigitalDisplay
from batgrl.gadgets.text import Text, new_cell


class DigitalClock(Text):
    def __init__(
        self,
        pos=(0, 0),
        twelve_hour=False,
        default_cell=new_cell(fg_color=BRIGHT_GREEN),
        **kwargs,
    ):
        super().__init__(
            size=(7, 52),
            pos=pos,
            default_cell=default_cell,
            **kwargs,
        )
        self.twelve_hour = twelve_hour

        for i in range(6):
            self.add_gadget(DigitalDisplay(pos=(0, i * 8 + i // 2 * 2)))

        self.canvas["char"][[2, -3], 16] = self.canvas["char"][[2, -3], 34] = "●"

    def on_add(self):
        super().on_add()
        self._update_task = asyncio.create_task(self._update_time())

    def on_remove(self):
        super().on_remove()
        self._update_task.cancel()

    def _formatted_time(self):
        hours, minutes, seconds = time.localtime()[3:6]

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
    """Display any key pressed."""

    def on_key(self, key_event):
        if len(key_event.key) == 1:
            self.show_char(key_event.key)
            return True


class DigitalClockApp(App):
    async def on_start(self):
        self.add_gadgets(DigitalClock(twelve_hour=True), TestDisplay(pos=(10, 0)))


if __name__ == "__main__":
    DigitalClockApp(title="Digital Clock Example").run()
