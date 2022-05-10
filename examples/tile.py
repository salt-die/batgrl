import asyncio
from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.tiled_image import TiledImage

LOGO_PATH = Path("images") / "python_discord_logo.png"
LOGO_FLAT = Path("images") / "logo_solo_flat_256.png"


class MyApp(App):
    async def on_start(self):
        tile_1 = Image(size=(10, 25), path=LOGO_PATH)
        tile_2 = Image(size=(9, 19), path=LOGO_FLAT)

        tiled_image = TiledImage(size=(25, 50), tile=tile_1)

        self.add_widget(tiled_image)

        await asyncio.sleep(5)

        tiled_image.tile = tile_2


MyApp(title="Tile Example").run()
