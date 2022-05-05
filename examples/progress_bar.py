import asyncio

from nurses_2.app import App
from nurses_2.widgets.progress_bar import ProgressBar


class MyApp(App):
    async def on_start(self):
        horizontal_bar = ProgressBar(size=(2, 100))
        vertical_bar = ProgressBar(size=(20, 2), pos=(3, 0), is_horizontal=False)

        self.add_widgets(horizontal_bar, vertical_bar)

        for i in range(500):
            horizontal_bar.progress = (i + 1) / 500
            vertical_bar.progress = (i + 1) / 500
            await asyncio.sleep(.1)


MyApp().run()
