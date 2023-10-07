import asyncio
from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.image import Image
from batgrl.gadgets.tiled_image import TiledImage

ASSETS = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS / "python_discord_logo.png"
LOGO_FLAT = ASSETS / "logo_solo_flat_256.png"


class TiledApp(App):
    async def on_start(self):
        tile_1 = Image(size=(10, 25), path=LOGO_PATH)
        tile_2 = Image(size=(9, 19), path=LOGO_FLAT)

        tiled_image = TiledImage(size=(25, 50), tile=tile_1)

        self.add_gadget(tiled_image)

        await asyncio.sleep(5)

        tiled_image.tile = tile_2


if __name__ == "__main__":
    TiledApp(title="Tile Example").run()
