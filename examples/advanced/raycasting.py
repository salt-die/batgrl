"""Showcase of batgrl's raycasters."""

import asyncio
from itertools import cycle, pairwise
from pathlib import Path
from time import perf_counter

import numpy as np
from batgrl.app import App
from batgrl.colors import GREEN
from batgrl.gadgets.raycaster import Raycaster
from batgrl.gadgets.text_raycaster import TextRaycaster
from batgrl.gadgets.video import Video
from batgrl.geometry import lerp
from batgrl.text_tools import new_cell
from batgrl.texture_tools import read_texture


def load_assets():
    assets = Path(__file__).parent.parent / "assets"

    yield assets / "spinner.gif"

    checker = assets / "checkered.png"
    yield read_texture(checker)

    python_sprite = assets / "pixel_python.png"
    yield read_texture(python_sprite)

    wall = assets / "wall.txt"
    yield np.array(
        [[int(char) for char in line] for line in wall.read_text().splitlines()],
        np.uint8,
    )

    tree = assets / "tree.txt"
    yield tree.read_text()


SPINNER, CHECKER, PYTHON, WALL, TREE = load_assets()
MAP = np.array(
    [
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 1, 1, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 0, 0, 0, 0, 0, 0, 0, 0, 1],
        [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    ],
    dtype=np.uint8,
)


class RaycasterApp(App):
    """A raycaster app."""

    async def on_start(self):
        points = np.array([[2.5, 2.5], [2.5, 7.5], [7.5, 7.5], [7.5, 2.5]])
        angles = [np.pi, np.pi / 2, 0, 3 * np.pi / 2]

        # To achieve an animated texture, we'll set the wall texture to this video's
        # texture while it plays.
        video = Video(source=SPINNER, size=(256, 256), blitter="full")
        video.play()
        raycaster = Raycaster(
            caster_map=MAP,
            wall_textures=[video.texture],
            camera_coord=points[0],
            camera_angle=angles[0],
            sprite_coords=points,
            sprite_indexes=np.zeros(4, np.uint8),
            sprite_textures=[PYTHON],
            ceiling=CHECKER,
            floor=CHECKER,
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
        )
        text_raycaster = TextRaycaster(
            caster_map=MAP,
            wall_textures=[WALL],
            camera_coord=points[0],
            camera_angle=angles[0],
            sprite_coords=points,
            sprite_indexes=np.zeros(4, np.uint8),
            sprite_textures=[TREE],
            default_cell=new_cell(fg_color=GREEN),
            size_hint={"height_hint": 1.0, "width_hint": 0.5},
            pos_hint={"x_hint": 0.5, "anchor": "left"},
        )
        self.add_gadgets(raycaster, text_raycaster)

        turn_duration = 0.75
        move_duration = 1.5
        last_time = perf_counter()
        elapsed = 0

        for i, j in pairwise(cycle(range(4))):
            u, v = angles[i], angles[j]
            if v > u:
                v -= 2 * np.pi

            while elapsed < turn_duration:
                current_time = perf_counter()
                elapsed += current_time - last_time
                last_time = current_time
                raycaster.camera_angle = lerp(u, v, elapsed / turn_duration)
                text_raycaster.camera_angle = raycaster.camera_angle
                raycaster.cast_rays()
                text_raycaster.cast_rays()
                await asyncio.sleep(0)

            raycaster.camera_angle = v
            elapsed -= turn_duration

            while elapsed < move_duration:
                current_time = perf_counter()
                elapsed += current_time - last_time
                last_time = current_time

                raycaster.camera_coord = lerp(
                    points[i], points[j], elapsed / move_duration
                )
                text_raycaster.camera_coord = raycaster.camera_coord
                raycaster.cast_rays()
                text_raycaster.cast_rays()
                await asyncio.sleep(0)

            raycaster.camera_coord = points[j]
            elapsed -= move_duration


if __name__ == "__main__":
    RaycasterApp(title="Raycasting Example").run()
