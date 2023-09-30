import asyncio
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.file_chooser import FileChooser
from nurses_2.widgets.text_widget import TextWidget

ASSETS = Path(__file__).parent.parent / "assets"


class FileApp(App):
    async def on_start(self):
        label = TextWidget(size=(1, 50), pos=(0, 26))

        def select_callback(path):
            label.add_str(f"{f'{path.name} selected!':<50}"[:50])

        fc = FileChooser(
            root_dir=ASSETS,
            size=(20, 25),
            size_hint={"height_hint": 1.0},
            select_callback=select_callback,
        )
        self.add_widgets(label, fc)

        await asyncio.sleep(5)

        fc.root_dir = ASSETS.parent.parent


if __name__ == "__main__":
    FileApp(title="File Chooser Example").run()
