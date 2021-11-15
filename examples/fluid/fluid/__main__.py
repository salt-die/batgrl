import numpy as np

from nurses_2.app import App
from nurses_2.colors import Color
from nurses_2.widgets.behaviors.auto_position_behavior import AutoPositionBehavior, Anchor
from nurses_2.widgets.graphic_widget import GraphicWidget

from .sph import SPHSolver

WATER_COLOR = Color.from_hex("1e1ea8")


class Fluid(AutoPositionBehavior, GraphicWidget):
    def __init__(self, *args, nparticles=400, **kwargs):
        super().__init__(*args, **kwargs)
        y, x = self.size
        self.sph_solver = SPHSolver((2 * y - 1, x - 1), nparticles)

    def on_press(self, key_press_event):
        match key_press_event.key:
            case "r":
                self.sph_solver.init_dam()
                return True

        return False

    def render(self, canvas_view, colors_view, rect):
        solver = self.sph_solver
        solver.step()

        self.texture[:] = self.default_bg_color

        positions = solver.state[:, :2]
        pressure = solver.state[:, -1]

        ys, xs = positions.astype(np.uint).T
        alphas = (255 / (1 + np.e**-(.125 * pressure))).astype(int)

        self.texture[ys, xs, :3] = WATER_COLOR
        self.texture[ys, xs, 3] = alphas

        return super().render(canvas_view, colors_view, rect)


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(
            Fluid(
                size=(20, 50),
                pos_hint=(.5, .5),
                anchor=Anchor.CENTER,
            )
        )


MyApp().run()
