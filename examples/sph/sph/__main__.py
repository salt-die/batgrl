import asyncio

import numpy as np

from nurses_2.app import App
from nurses_2.colors import Color, ColorPair, BLACK, BLACK_ON_BLACK, WHITE_ON_BLACK
from nurses_2.io import MouseButton
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.graphic_widget import GraphicWidget, Anchor
from nurses_2.widgets.slider import Slider

from .solver import SPHSolver

WATER_COLOR = Color.from_hex("1e1ea8")
FILL_COLOR = Color.from_hex("2fa399")
WATER_ON_BLACK = ColorPair.from_colors(WATER_COLOR, BLACK)


class SPH(GraphicWidget):
    def __init__(self, nparticles, is_transparent=False, **kwargs):
        super().__init__(is_transparent=is_transparent, **kwargs)
        y, x = self.size
        self.sph_solver = SPHSolver(nparticles, (2 * y - 1, x - 1))
        self._update_task = asyncio.create_task(self._update())

    def on_keypress(self, key_press_event):
        match key_press_event.key:
            case "r":
                self.sph_solver.init_dam()
                return True

        return False

    def on_mouse(self, mouse_event):
        if (
            mouse_event.button is MouseButton.NO_BUTTON
            or not self.collides_point(mouse_event.position)
        ):
            return False

        # Apply a force from click to every particle in the solver.
        my, mx = self.to_local(mouse_event.position)

        relative_positions = self.sph_solver.state[:, :2] - (2 * my, mx)

        self.sph_solver.state[:, 2:4] += (
            1e2 * relative_positions
            / np.linalg.norm(relative_positions, axis=-1, keepdims=True)
        )

        return True

    async def _update(self):
        while True:
            solver = self.sph_solver
            solver.step()

            positions = solver.state[:, :2]
            ys, xs = positions.astype(int).T

            self.texture[:] = self.default_color
            self.texture[ys, xs, :3] = WATER_COLOR

            await asyncio.sleep(0)


class MyApp(App):
    async def on_start(self):
        WIDTH = 51
        HWIDTH = WIDTH // 2

        container = TextWidget(
            size=(26, WIDTH),
            pos_hint=(.5, .5),
            anchor=Anchor.CENTER,
            default_color_pair=BLACK_ON_BLACK,
        )
        container.colors[:6] = WHITE_ON_BLACK

        fluid = SPH(225, pos=(6, 0), size=(20, 50))
        solver = fluid.sph_solver

        slider_settings = {
            "width": HWIDTH,
            "fill_color": FILL_COLOR,
            "default_color_pair": WATER_ON_BLACK,
        }

        adjust_H = Slider(
            pos=(1, 0),
            min=.4,
            max=3.5,
            start_value=solver.H,
            callback=lambda value: (
                setattr(solver, "H", value),
                container.add_text(
                    f'{f"Smoothing Length: {round(solver.H, 4)}":<{HWIDTH}}',
                ),
            ),
            **slider_settings,
        )

        adjust_GAS_CONST = Slider(
            pos=(1, HWIDTH + 1),
            min=500.0,
            max=4000.0,
            start_value=solver.GAS_CONST,
            callback=lambda value: (
                setattr(solver, "GAS_CONST", value),
                container.add_text(
                    f'{f"Gas Constant: {round(solver.GAS_CONST, 4)}":<{HWIDTH}}',
                    column=HWIDTH,
                ),
            ),
            **slider_settings,
        )

        adjust_REST_DENS = Slider(
            pos=(3, 0),
            min=150.0,
            max=500.0,
            start_value=solver.REST_DENS,
            callback=lambda value: (
                setattr(solver, "REST_DENS", value),
                container.add_text(
                    f'{f"Rest Density: {round(solver.REST_DENS, 4)}":<{HWIDTH}}',
                    row=2,
                ),
            ),
            **slider_settings,
        )

        adjust_VISC = Slider(
            pos=(3, HWIDTH + 1),
            min=0.0,
            max=5000.0,
            start_value=solver.VISC,
            callback=lambda value: (
                setattr(solver, "VISC", value),
                container.add_text(
                    f'{f"Viscosity: {round(solver.VISC, 4)}":<{HWIDTH}}',
                    row=2,
                    column=HWIDTH,
                ),
            ),
            **slider_settings,
        )

        adjust_MASS = Slider(
            pos=(5, 0),
            min=10.0,
            max=500.0,
            start_value=solver.MASS,
            callback=lambda value: (
                setattr(solver, "MASS", value),
                container.add_text(
                    f'{f"Mass: {round(solver.MASS, 4)}":<{HWIDTH}}',
                    row=4,
                ),
            ),
            **slider_settings,
        )

        adjust_DT = Slider(
            pos=(5, HWIDTH + 1),
            min=.001,
            max=.03,
            start_value=solver.DT,
            callback=lambda value: (
                setattr(solver, "DT", value),
                container.add_text(
                    f'{f"DT: {round(solver.DT, 4)}":<{HWIDTH}}',
                    row=4,
                    column=HWIDTH,
                ),
            ),
            **slider_settings,
        )

        container.add_widgets(
            fluid,
            adjust_H,
            adjust_GAS_CONST,
            adjust_REST_DENS,
            adjust_VISC,
            adjust_MASS,
            adjust_DT,
        )

        self.add_widget(container)


MyApp(title="Smooth Particle Hydrodynamics Example").run()
