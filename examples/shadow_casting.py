from itertools import cycle

import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import rainbow_gradient, AColor, gradient, WHITE, BLUE, RED
from nurses_2.io import MouseEventType
from nurses_2.widgets.shadow_caster import (
    AGRAY,
    Point,
    LightIntensity,
    LightSource,
    ShadowCaster,
)

MAP = np.random.randint(0, 150, (100, 100), dtype=np.uint8)
MAP[MAP >= 7] = 0
WHITE_TO_BLUE = cycle(gradient(WHITE, BLUE, 10) + gradient(BLUE, WHITE, 10))
WHITE_TO_RED = cycle(gradient(WHITE, RED, 15) + gradient(RED, WHITE, 15))


class MyShadowCaster(ShadowCaster):
    def resize(self, size):
        super().resize(size)
        h, w = size
        self.light_sources[1].pos = Point(h, w // 2)

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_MOVE
            and self.collides_point(mouse_event.position)
        ):
            y, x = self.to_local(mouse_event.position)
            self.light_sources[0].pos = Point(y * 2, x)

    def on_press(self, key_press_event):
        y, x = self.light_sources[1].pos

        match key_press_event.key:
            case "up":
                self.light_sources[1].pos = Point(y - 1, x)
            case "down":
                self.light_sources[1].pos = Point(y + 1, x)
            case "left":
                self.light_sources[1].pos = Point(y, x - 1)
            case "right":
                self.light_sources[1].pos = Point(y, x + 1)
            case _:
                return False

        return True

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self.light_sources[0].intensity = LightIntensity.from_color(next(WHITE_TO_BLUE))
        self.light_sources[1].intensity = LightIntensity.from_color(next(WHITE_TO_RED))
        self.cast_shadows()

        super().render(canvas_view, colors_view, source)


run_widget_as_app(
    MyShadowCaster,
    size_hint=(1.0, 1.0),
    map=MAP,
    tile_colors=[AGRAY] + rainbow_gradient(7, color_type=AColor),
    light_sources=[LightSource(), LightSource()],
    ambient_light=.05,
    radius=40,
)
