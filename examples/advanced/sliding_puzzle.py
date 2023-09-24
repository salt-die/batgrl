import asyncio
from pathlib import Path

from nurses_2.app import run_widget_as_app
from nurses_2.colors import ABLACK, AWHITE
from nurses_2.io import MouseButton, MouseEventType
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.texture_tools import read_texture, resize_texture

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_LOGO = ASSETS / "python_discord_logo.png"

SIZE = H, W = 40, 80  # Each dimension should be divisible by 4
EMPTY_PIECE = object()


class _SlidingPiece(GraphicWidget):
    def on_mouse(self, mouse_event):
        if (
            not self.parent._sliding
            and mouse_event.button is MouseButton.LEFT
            and mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and self.collides_point(mouse_event.position)
        ):
            y, x = self._grid_pos
            grid = self.parent._grid

            for ey, ex in ((y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)):
                if grid.get((ey, ex)) is EMPTY_PIECE:
                    self._grid_pos = ey, ex
                    grid[ey, ex] = self
                    grid[y, x] = EMPTY_PIECE
                    self.parent._sliding = True
                    asyncio.create_task(
                        self.tween(
                            duration=0.5,
                            on_complete=lambda: setattr(self.parent, "_sliding", False),
                            pos=(ey * self.height, ex * self.width),
                        )
                    )
                    break

            return True


class SlidingPuzzle(GraphicWidget):
    def __init__(self, path: Path, **kwargs):
        super().__init__(**kwargs)

        sprite = resize_texture(read_texture(path), (H * 2, W))

        self._grid = {}

        h, w = H // 4, W // 4
        for y in range(4):
            for x in range(4):
                if y == 3 and x == 3:
                    self._grid[y, x] = EMPTY_PIECE
                else:
                    piece = _SlidingPiece(size=(h, w), pos=(y * h, x * w))
                    piece._grid_pos = y, x
                    piece.texture[:] = sprite[
                        piece.top * 2 : piece.bottom * 2, piece.left : piece.right
                    ]
                    piece.texture[0] = piece.texture[:, 0] = AWHITE
                    piece.texture[-1] = piece.texture[:, -1] = ABLACK
                    self._grid[y, x] = piece
                    self.add_widget(piece)

        self._sliding = False


if __name__ == "__main__":
    run_widget_as_app(SlidingPuzzle(PATH_TO_LOGO, size=SIZE))
