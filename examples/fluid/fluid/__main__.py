import numpy as np

from nurses_2.app import App
from nurses_2.colors import AColor
from nurses_2.data_structures import Size
from nurses_2.widgets.behaviors.auto_resize_behavior import AutoSizeBehavior
from nurses_2.widgets.graphic_widget import GraphicWidget

from .sph import SPHSolver

WATER_COLOR = AColor.from_hex("1e1ea8")


class Fluid(AutoSizeBehavior, GraphicWidget):
    def __init__(self, *args, nparticles=1000, **kwargs):
        super().__init__(*args, **kwargs)
        y, x = self.size
        self.sph_solver = SPHSolver((2 * y, x), nparticles)

    def resize(self, size: Size):
        h, w = self.size

        self.sph_solver.resize((2 * h, w))

        super().resize(size)

    def render(self, canvas_view, colors_view, rect):
        self.sph_solver.step()

        self.texture[:] = self.default_bg_color

        y, x = self.sph_solver.state[:, :2].astype(int).T
        self.texture[y, x] = WATER_COLOR

        return super().render(canvas_view, colors_view, rect)


class MyApp(App):
    async def on_start(self):
        self.root.add_widget(Fluid())
        # Why do I need to manually call resize?
        self.root.children[0].resize(self.root.size)


MyApp().run()
