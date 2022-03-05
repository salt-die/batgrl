import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import rainbow_gradient, AColor
from nurses_2.io import MouseEventType
from nurses_2.widgets.shadow_caster import ShadowCaster, Point, AGRAY

MAP = np.random.randint(0, 200, (100, 100), dtype=np.uint8)
MAP[MAP >= 7] = 0


class MouseOriginShadowCaster(ShadowCaster):
    def resize(self, size):
        super().resize(size)
        h, w = size
        self.light_sources[1] = Point(h // 2, w // 2)
        self.cast_shadows()

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_MOVE
            and self.collides_point(mouse_event.position)
        ):
            self.light_sources[0] = self.to_local(mouse_event.position)
            self.cast_shadows()


run_widget_as_app(
    MouseOriginShadowCaster,
    size_hint=(1.0, 1.0),
    map=MAP,
    tile_colors=[AGRAY] + rainbow_gradient(7, color_type=AColor),
    light_sources=[Point(0, 0), Point(0, 0)],
    ambient_light=.05,
    radius=40,
)