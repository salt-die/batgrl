from nurses_2.app import App
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.text_widget import TextWidget


class FileApp(App):
    async def on_start(self):
        label = TextWidget(size=(1, 50), pos=(0, 26))
        select_callback = lambda path: label.add_text(f"{f'{path.name} selected!':<50}"[:50])

        self.add_widgets(label, FileChooser(size=(20, 25), size_hint=(1.0, None), select_callback=select_callback))


FileApp().run()
