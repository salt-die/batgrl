import asyncio

from nurses_2.app import App
from nurses_2.widgets import Widget
from nurses_2.io import PasteEvent

class PasteWidget(Widget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._clear_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    async def _clear_paste(self):
        await asyncio.sleep(5)
        self.canvas[:] = " "

    def on_paste(self, paste_event: PasteEvent):
        self.add_text("Got paste:")

        for i, line in enumerate(paste_event.paste.splitlines(), start=1):
            self.add_text(line[:self.width], row=i)

        if self._clear_task.done():
            self._clear_task = asyncio.create_task(self._clear_paste())


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(PasteWidget(size=(10, 100)))


MyApp().run()
