from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.split_layout import HSplitLayout, VSplitLayout

IMAGE_DIR = Path("images")
PATH_TO_LOGO_FLAT = IMAGE_DIR / "logo_solo_flat_256.png"
PATH_TO_LOGO_FULL = IMAGE_DIR / "python_discord_logo.png"


class MyApp(App):
    async def on_start(self):
        image_tl = Image(path=PATH_TO_LOGO_FLAT, size_hint=(1.0, 1.0))
        image_tr = Image(path=PATH_TO_LOGO_FULL, size_hint=(1.0, 1.0))
        image_bl = Image(path=PATH_TO_LOGO_FULL, size_hint=(1.0, 1.0))
        image_br = Image(path=PATH_TO_LOGO_FLAT, size_hint=(1.0, 1.0))

        split_layout = VSplitLayout(split_row=10, size_hint=(1.0, 1.0))
        top_split_layout = HSplitLayout(split_col=10, size_hint=(1.0, 1.0))
        bottom_split_layout = HSplitLayout(split_col=10, size_hint=(1.0, 1.0), anchor_left_pane=False)

        split_layout.top_pane.add_widget(top_split_layout)
        split_layout.bottom_pane.add_widget(bottom_split_layout)

        top_split_layout.left_pane.add_widget(image_tl)
        top_split_layout.right_pane.add_widget(image_tr)

        bottom_split_layout.left_pane.add_widget(image_bl)
        bottom_split_layout.right_pane.add_widget(image_br)

        self.add_widget(split_layout)


MyApp(title="Split Layout Example").run()
