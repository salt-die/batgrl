from nurses_2.app import App
from nurses_2.colors import AColor
from nurses_2.widgets.behaviors.auto_position_behavior import AutoPositionBehavior, Anchor
from nurses_2.widgets import Widget
from nurses_2.widgets.graphic_widget import GraphicWidget

from .sph import SPHSolver

WATER_COLOR = AColor.from_hex("1e1ea8")


class Fluid(GraphicWidget):
    def __init__(self, *args, nparticles=150, **kwargs):
        super().__init__(*args, **kwargs)
        y, x = self.size
        self.sph_solver = SPHSolver((2 * y, x), nparticles)

    def on_press(self, key_press_event):
        match key_press_event.key:
            case "r":
                self.sph_solver.init_dam()
                return True

        return False

    def render(self, canvas_view, colors_view, rect):
        self.sph_solver.step()

        self.texture[:] = self.default_bg_color

        y, x = self.sph_solver.state[:, :2].astype(int).T
        self.texture[y, x] = WATER_COLOR

        return super().render(canvas_view, colors_view, rect)


class Label(AutoPositionBehavior, Widget):
    ...

class MyApp(App):
    async def on_start(self):
        label = Label(
            size=(11, 30),
            pos_hint=(.5, .5),
            anchor=Anchor.CENTER,
        )
        label.add_widget(Fluid(size=(10, 30), pos=(1, 0)))
        label.add_text(f"{'Smooth Particle Hydrodynamics':^30}")

        self.root.add_widget(label)


MyApp().run()
