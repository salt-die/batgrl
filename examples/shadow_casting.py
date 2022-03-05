from itertools import cycle

import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import rainbow_gradient, AColor
from nurses_2.io import MouseEventType
from nurses_2.widgets.shadow_caster import (
    AGRAY,
    Point,
    LightIntensity,
    LightSource,
    ShadowCaster,
    NO_LIGHT,
)

MAP = np.random.randint(0, 200, (100, 100), dtype=np.uint8)
MAP[MAP >= 7] = 0
RAINBOW = cycle(rainbow_gradient(20))


class MouseOriginShadowCaster(ShadowCaster):
    def resize(self, size):
        super().resize(size)
        h, w = size
        _, intensity = self.light_sources[1]
        self.light_sources[1] = LightSource(
            Point(h // 2, w // 2),
            intensity,
        )

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_MOVE
            and self.collides_point(mouse_event.position)
        ):
            _, intensity = self.light_sources[0]
            self.light_sources[0] = LightSource(
                self.to_local(mouse_event.position),
                intensity,
            )

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        intensity = LightIntensity.from_color(next(RAINBOW))
        self.light_sources = [LightSource(pos, intensity) for pos, _ in self.light_sources]
        self.cast_shadows()

        super().render(canvas_view, colors_view, source)


run_widget_as_app(
    MouseOriginShadowCaster,
    size_hint=(1.0, 1.0),
    map=MAP,
    tile_colors=[AGRAY] + rainbow_gradient(7, color_type=AColor),
    light_sources=[LightSource((0, 0), NO_LIGHT)] * 2,
    ambient_light=.05,
    radius=40,
)
