"""
A visualization of the Arctic Circle Theorem, idea from:
    (The ARCTIC CIRCLE THEOREM or Why do physicists play dominoes?)
    https://www.youtube.com/watch?v=Yy7Q8IWNfHM
"""
import numpy as np
import cv2

from nurses_2.app import run_widget_as_app
from nurses_2.io import MouseEvent, MouseEventType, KeyPressEvent
from nurses_2.widgets.graphic_widget import GraphicWidget, Interpolation

N, E, S, W = 1, 2, 3, 4
COLORS = np.array([
    [244, 241, 222, 255],
    [224, 122, 95, 255],
    [61, 64, 91, 255],
    [129, 178, 154, 255],
    [242, 204, 143, 255],
], dtype=np.uint8)

def remove_collisions(tiles):
    up_down = (tiles[:-1] == S) & (tiles[1:] == N)
    left_right = (tiles[:, :-1] == E) & (tiles[:, 1:] == W)

    tiles[:-1][up_down] = 0
    tiles[1:][up_down] = 0
    tiles[:, :-1][left_right] = 0
    tiles[:, 1:][left_right] = 0

def dance(tiles):
    d, _ = tiles.shape
    new_tiles = np.zeros((d + 2, d + 2), dtype=np.uint8)

    new_tiles[:-2, 1: -1][tiles == N] = N
    new_tiles[2: , 1: -1][tiles == S] = S
    new_tiles[1: -1, :-2][tiles == W] = W
    new_tiles[1: -1, 2: ][tiles == E] = E
    return new_tiles

def fill(tiles):
    d, _ = tiles.shape
    half = d // 2
    offset = half - .5

    for y, x in np.argwhere(tiles == 0):
        if abs(y - offset) + abs(x - offset) <= half and tiles[y, x] == 0:
            if round(np.random.random()):
                tiles[y, x: x + 2] = N
                tiles[y + 1, x: x + 2] = S
            else:
                tiles[y: y + 2, x] = W
                tiles[y: y + 2, x + 1] = E


class AztecGold(GraphicWidget):
    def __init__(self, **kwargs):
        self.tiles = np.zeros((2, 2), dtype=np.uint8)
        fill(self.tiles)
        super().__init__(**kwargs)

    def on_size(self):
        h, w = self.size
        self.texture = cv2.resize(
            COLORS[self.tiles],
            (w, h * 2),
            interpolation=self.interpolation,
        )

    def on_click(self, mouse_event: MouseEvent) -> bool | None:
        match mouse_event.event_type:
            case MouseEventType.MOUSE_DOWN:
                remove_collisions(self.tiles)
                self.tiles = dance(self.tiles)
                fill(self.tiles)
                self.on_size()

    def on_press(self, key_press_event: KeyPressEvent) -> bool | None:
        match key_press_event.key:
            case "r":
                self.tiles = np.zeros((2, 2), dtype=np.uint8)
                fill(self.tiles)
                self.on_size()


run_widget_as_app(AztecGold, size_hint=(1.0, 1.0), interpolation=Interpolation.NEAREST)
