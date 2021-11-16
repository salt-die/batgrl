import numpy as np

from nurses_2.app import App
from nurses_2.colors import Color, color_pair, BLACK, BLACK_ON_BLACK
from nurses_2.widgets import Widget
from nurses_2.widgets.behaviors.auto_position_behavior import AutoPositionBehavior, Anchor
from nurses_2.widgets.graphic_widget import GraphicWidget
from nurses_2.widgets.slider import Slider

from .sph import SPHSolver

WATER_COLOR = Color.from_hex("1e1ea8")
WATER_ON_BLACK = color_pair(WATER_COLOR, BLACK)


class Fluid(GraphicWidget):
    def __init__(self, *args, nparticles=1000, **kwargs):
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

        positions = solver.state[:, :2]
        ys, xs = positions.astype(int).T

        pressure = solver.state[:, -1]
        alphas = (255 / (1 + np.e**-(.125 * pressure))).astype(int)

        self.texture[:] = self.default_bg_color
        self.texture[ys, xs, :3] = WATER_COLOR
        self.texture[ys, xs, 3] = alphas

        return super().render(canvas_view, colors_view, rect)


class AutoPositionWidget(AutoPositionBehavior, Widget):
    ...


class MyApp(App):
    async def on_start(self):
        WIDTH = 51
        HWIDTH = WIDTH // 2
        container = AutoPositionWidget(
            size=(26, WIDTH),
            pos_hint=(.5, .5),
            anchor=Anchor.CENTER,
            default_color_pair=BLACK_ON_BLACK
        )
        container.colors[:6, :, :3] = 255

        fluid = Fluid(pos=(6, 0), size=(20, 50))
        solver = fluid.sph_solver

        adjust_H = Slider(
            width=HWIDTH,
            pos=(1, 0),
            min=.4,
            max=1.44,
            proportion=.04711,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "H", value),
                container.add_text(f'{f"H: {solver.H}":<{HWIDTH}}'[:HWIDTH]),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        adjust_GAS_CONST = Slider(
            width=HWIDTH,
            pos=(1, HWIDTH + 1),
            min=100.0,
            max=4000.0,
            proportion=.02564,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "GAS_CONST", value),
                container.add_text(f'{f"GAS_CONST: {solver.GAS_CONST}":<{HWIDTH}}'[:HWIDTH], column=HWIDTH),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        adjust_REST_DENS = Slider(
            width=HWIDTH,
            pos=(3, 0),
            min=40.0,
            max=400.0,
            proportion=.44444,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "REST_DENS", value),
                container.add_text(f'{f"REST_DENS: {solver.REST_DENS}":<{HWIDTH}}'[:HWIDTH], row=2),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        adjust_POLYF = Slider(
            width=HWIDTH,
            pos=(3, HWIDTH + 1),
            min=1.0,
            max=10.0,
            proportion=0.0,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "POLYF", value),
                container.add_text(f'{f"POLY: {solver.POLYF}":<{HWIDTH}}'[:HWIDTH], row=2, column=HWIDTH),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        adjust_VISCF = Slider(
            width=HWIDTH,
            pos=(5, 0),
            min=1000.0,
            max=5000.0,
            proportion=1.0,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "VISCF", value),
                container.add_text(f'{f"VISC: {solver.VISCF}":<{HWIDTH}}'[:HWIDTH], row=4),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        adjust_SPIKYF = Slider(
            width=HWIDTH,
            pos=(5, HWIDTH + 1),
            min=-10.0,
            max=-1.0,
            proportion=.55555,
            handle_color=WATER_COLOR,
            callback=lambda value: (
                setattr(solver, "SPIKYF", value),
                container.add_text(f'{f"SPIKY: {solver.SPIKYF}":<{HWIDTH}}'[:HWIDTH], row=4, column=HWIDTH),
            ),
            default_color_pair=WATER_ON_BLACK,
        )

        container.add_widgets(
            fluid,
            adjust_H,
            adjust_GAS_CONST,
            adjust_REST_DENS,
            adjust_POLYF,
            adjust_VISCF,
            adjust_SPIKYF,
        )

        self.root.add_widget(container)


MyApp().run()
