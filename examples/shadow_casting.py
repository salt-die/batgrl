import asyncio
from itertools import cycle

import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import rainbow_gradient, AColor, gradient, WHITE, BLUE, RED
from nurses_2.io import MouseEventType
from nurses_2.widgets.shadow_caster import (
    AGRAY,
    Camera,
    Point,
    LightIntensity,
    LightSource,
    ShadowCaster,
)

MAP = np.random.randint(0, 150, (100, 100), dtype=np.uint8)
MAP[MAP >= 7] = 0
WHITE_TO_BLUE = cycle(map(
    LightIntensity.from_color,
    gradient(WHITE, BLUE, 10) + gradient(BLUE, WHITE, 10),
))
WHITE_TO_RED = cycle(map(
    LightIntensity.from_color,
    gradient(WHITE, RED, 15) + gradient(RED, WHITE, 15),
))


class MyShadowCaster(ShadowCaster):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._update_task = asyncio.create_task(self._update())

    async def _update(self):
        while True:
            self.light_sources[0].intensity = next(WHITE_TO_BLUE)
            self.light_sources[1].intensity = next(WHITE_TO_RED)
            self.cast_shadows()
            await asyncio.sleep(0)

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_MOVE
            and self.collides_point(mouse_event.position)
        ):
            self.light_sources[0].coords = self.to_map_coords(self.to_local(mouse_event.position))

    def on_keypress(self, key_press_event):
        y, x = self.camera.pos

        match key_press_event.key:
            case "up":
                self.camera.pos = Point(y - 1, x)
            case "down":
                self.camera.pos = Point(y + 1, x)
            case "left":
                self.camera.pos = Point(y, x - 1)
            case "right":
                self.camera.pos = Point(y, x + 1)
            case _:
                return False

        return True


run_widget_as_app(
    MyShadowCaster,
    size_hint=(1.0, 1.0),
    map=MAP,
    camera=Camera((0, 0), (50, 50)),
    tile_colors=[AGRAY] + rainbow_gradient(7, color_type=AColor),
    light_sources=[LightSource(), LightSource(coords=(50, 50))],
    ambient_light=.05,
    radius=40,
)
