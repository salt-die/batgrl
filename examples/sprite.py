import asyncio
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.graphic_widget_data_structures import Sprite
from nurses_2.widgets.graphic_widget import GraphicWidget

THIS_DIR = Path(__file__).parent
IMAGE_DIR = THIS_DIR / Path("images")
PATH_TO_LOGO_FULL = IMAGE_DIR / "python_discord_logo.png"
sprite = Sprite.from_image(PATH_TO_LOGO_FULL).resize((10, 20))


class SpriteApp(App):
    async def on_start(self):
        graphic = GraphicWidget(size_hint=(1.0, 1.0))
        self.add_widget(graphic)

        for i in range(20):
            graphic.texture[:] = 0, 0, 0, 255
            sprite.paint(graphic.texture, pos=(i % 2, i))

            await asyncio.sleep(.1)


SpriteApp(title="Sprite Test").run()
