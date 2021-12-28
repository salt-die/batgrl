import asyncio

from nurses_2.app import App
from nurses_2.widgets.text_widget import TextWidget

class ShowKeyPress(TextWidget):
    current_row = 0

    def on_press(self, key_press_event):
        if self.current_row == self.height:
            self.current_row = 0

        row = self.current_row

        self.add_text(f"Got Press: {key_press_event!r}", row)
        asyncio.create_task(self.clear_row(row))

        self.current_row += 1

    async def clear_row(self, row):
        await asyncio.sleep(5)
        self.canvas[row] = " "


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(ShowKeyPress(size_hint=(1.0, 1.0)))

MyApp().run()
