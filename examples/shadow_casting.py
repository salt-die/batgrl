import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.io import MouseEventType
from nurses_2.widgets.shadow_caster import ShadowCaster, Point, Restrictiveness

MAP = np.random.random((100, 100))
MAP = (MAP < .08).astype(np.uint8)


class MouseOriginShadowCaster(ShadowCaster):
    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_MOVE
            and self.collides_point(mouse_event.position)
        ):
            y, x = self.to_local(mouse_event.position)
            self.origin = Point(y * 2, x)

    def render(self, canvas_view, colors_view, source: tuple[slice, slice]):
        self.update_visibility()
        super().render(canvas_view, colors_view, source)


run_widget_as_app(
    MouseOriginShadowCaster,
    size_hint=(1.0, 1.0),
    map=MAP,
    ambient_light=.05,
    light_decay=lambda d: 2 if d == 0 else 2 / d,
    radius=40,
    restrictiveness=Restrictiveness.MODERATE,
)