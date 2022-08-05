import asyncio
from pathlib import Path
from time import monotonic

import nurses_2.colors as colors
from nurses_2.app import App
from nurses_2.colors import AWHITE
from nurses_2.io import MouseEvent, MouseEventType, MouseButton
from nurses_2.widgets.graphic_widget import GraphicWidget, Sprite, Size, Point
from nurses_2.widgets.scroll_view import ScrollView

THIS_DIR = Path(__file__).parent
TILES_PATH = THIS_DIR / "images" / "isometric_demo.png"
WATER_TILE_PATH = THIS_DIR / "frames" / "water"

WORLD_SIZE = Size(5, 5)
ORIGIN = Point(0, 2)
TILE_SIZE = TH, TW = Size(20, 40)

TILE_SHEET = Sprite.from_image(TILES_PATH)
HIGHLIGHTED_TILE = Sprite(TILE_SHEET.texture[:TH, :TW])
BLANK_TILE       = Sprite(TILE_SHEET.texture[:TH, TW:2 * TW])
GRASS_TILE       = Sprite(TILE_SHEET.texture[:TH, 2 * TW:3 * TW])
BODGE_TILE       = Sprite(TILE_SHEET.texture[:TH, 3 * TW:])
TREE_TILE        = Sprite(TILE_SHEET.texture[TH:, :TW])
TREE_2_TILE      = Sprite(TILE_SHEET.texture[TH:, TW:2 * TW])
SAND_TILE        = Sprite(TILE_SHEET.texture[2 * TH:, 2 * TW:3 * TW])
WATER_TILES = [
    Sprite.from_image(path)
    for path in sorted(WATER_TILE_PATH.iterdir(), key=lambda file: file.name)
]

TILES = (
    BLANK_TILE,
    GRASS_TILE,
    TREE_TILE,
    TREE_2_TILE,
    WATER_TILES,
    SAND_TILE,
)


class WorldWidget(GraphicWidget):
    def __init__(self):
        wh, ww = WORLD_SIZE
        th, tw = TILE_SIZE

        super().__init__(
            size=(wh * th // 2, ww * tw),
            default_color=AWHITE,
        )

        self.tile_map = [[0 for _ in range(ww)] for _ in range(wh)]

        self.selected_tile = 666, 666

        self.paint_world()

        self._update_world_task = asyncio.create_task(self._update_world())

    def iso_tile_to_uv(self, y, x):
        h, w = TILE_SIZE
        return (
            ORIGIN.y * h + (x + y) * h // 2,
            ORIGIN.x * w + (x - y) * w // 2,
        )

    async def _update_world(self):
        while True:
            await asyncio.sleep(1/12)
            self.paint_world()

    def paint_world(self):
        self.texture[:] = self.default_color
        water_tx = int(monotonic() * 12) % len(WATER_TILES)

        for y, row in enumerate(self.tile_map):
            for x, i in enumerate(row):
                tile = TILES[i]
                if tile is WATER_TILES:
                    tile = WATER_TILES[water_tx]

                ty, tx = self.iso_tile_to_uv(y, x)

                if tile is TREE_TILE or tile is TREE_2_TILE:
                    GRASS_TILE.paint(self.texture, (ty, tx))
                    if (y, x) == self.selected_tile:
                        HIGHLIGHTED_TILE.paint(self.texture, (ty, tx))

                    ty -= TILE_SIZE.height
                    tile.paint(self.texture, (ty, tx))
                else:
                    tile.paint(self.texture, (ty, tx))
                    if (y, x) == self.selected_tile:
                        HIGHLIGHTED_TILE.paint(self.texture, (ty, tx))


    def on_click(self, mouse_event: MouseEvent) -> bool | None:
        if (
            mouse_event.button is MouseButton.MIDDLE
            or not self.collides_point(mouse_event.position)
        ):
            return

        if mouse_event.event_type is MouseEventType.MOUSE_DOWN:
            y, x = self.selected_tile

            if 0 <= y < WORLD_SIZE.height and 0 <= x < WORLD_SIZE.width:
                if mouse_event.button is MouseButton.LEFT:
                    self.tile_map[y][x] += 1
                elif mouse_event.button is MouseButton.RIGHT:
                    self.tile_map[y][x] += -1

                self.tile_map[y][x] %= len(TILES)
                self.paint_world()

            return True

        y, x = self.to_local(mouse_event.position)
        y *= 2

        tile_y, tile_offset_y = divmod(y, TILE_SIZE.height)
        tile_x, tile_offset_x = divmod(x, TILE_SIZE.width)

        selected_tile_y = (tile_y - ORIGIN.y) - (tile_x - ORIGIN.x)
        selected_tile_x = (tile_y - ORIGIN.y) + (tile_x - ORIGIN.x)

        color = *BODGE_TILE.texture[tile_offset_y, tile_offset_x, :3],
        match color:
            case colors.RED:
                selected_tile_x -= 1
            case colors.YELLOW:
                selected_tile_x += 1
            case colors.BLUE:
                selected_tile_y -= 1
            case colors.GREEN:
                selected_tile_y += 1

        new_selected_tile = selected_tile_y, selected_tile_x
        if new_selected_tile != self.selected_tile:
            self.selected_tile = new_selected_tile
            self.paint_world()


class IsoTileApp(App):
    async def on_start(self):
        sv = ScrollView(
            size_hint=(1.0, 1.0),
            show_vertical_bar=False,
            show_horizontal_bar=False,
            mouse_button=MouseButton.MIDDLE,
        )
        sv.add_widget(WorldWidget())
        self.add_widget(sv)


if __name__ == "__main__":
    IsoTileApp(title="IsoTiles").run()
