import asyncio
import math
import random
from itertools import chain

import numpy as np
from batgrl.app import App
from batgrl.colors import (
    ACYAN,
    AMAGENTA,
    AWHITE,
    BLACK,
    BLUE,
    NEPTUNE_PRIMARY_BG,
    NEPTUNE_PRIMARY_FG,
    RED,
    WHITE,
    gradient,
)
from batgrl.gadgets.behaviors.grabbable import Grabbable
from batgrl.gadgets.gadget import Gadget, clamp
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.shadow_caster import ShadowCaster
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.toggle_button import ToggleButton

PANEL_WIDTH = 23
WHITE_TO_RED = gradient(WHITE, RED, n=PANEL_WIDTH)
WHITE_TO_BLUE = gradient(WHITE, BLUE, n=PANEL_WIDTH)
BLACK_TO_WHITE = gradient(BLACK, WHITE, n=PANEL_WIDTH)


class Selector(Grabbable, Text):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicator = Text(
            size=(1, 1), default_cell=new_cell(fg_color=BLACK, bg_color=WHITE)
        )
        self.add_gadget(self.indicator)
        self.callback = None

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        self.indicator.x = clamp(self.to_local(mouse_event.pos).x, 0, self.width - 1)
        if self.callback:
            self.callback(self.indicator.x)


class ShadowCasterApp(App):
    async def on_start(self):
        caster_map = np.zeros((34, 34), np.uint8)

        caster = ShadowCaster(
            size=(17, 34),
            caster_map=caster_map,
            camera_pos=(0, 0),
            camera_size=(34, 34),
            tile_colors=[AWHITE, ACYAN, AMAGENTA],
            light_coords=[(0, 0), (0, 0)],
            light_colors=[WHITE, WHITE],
            radius=40,
            is_transparent=False,
        )

        label_kwargs = dict(
            default_cell=new_cell(
                fg_color=NEPTUNE_PRIMARY_FG, bg_color=NEPTUNE_PRIMARY_BG
            )
        )
        button_kwargs = dict(size=(1, PANEL_WIDTH), group=1)
        slider_kwargs = dict(
            default_cell=new_cell(ord=ord("━"), bg_color=NEPTUNE_PRIMARY_BG),
            size=(1, PANEL_WIDTH),
        )

        def make_toggle_callback(mode):
            def callback(toggle_state):
                if toggle_state == "on":
                    caster.restrictiveness = mode

            return callback

        button_label = Text(**label_kwargs)
        button_label.set_text("Caster Restrictiveness:")

        button_a = ToggleButton(
            label="Permissive",
            callback=make_toggle_callback("permissive"),
            **button_kwargs,
        )
        button_b = ToggleButton(
            label="Moderate",
            callback=make_toggle_callback("moderate"),
            **button_kwargs,
        )
        button_c = ToggleButton(
            label="Restrictive",
            callback=make_toggle_callback("restrictive"),
            **button_kwargs,
        )

        def make_slider_callback(light_source, colors):
            def callback(i):
                caster.light_colors[light_source] = colors[round(i)]

            return callback

        slider_a = Selector(**slider_kwargs)
        slider_a.callback = make_slider_callback(0, WHITE_TO_RED)
        slider_a.canvas["fg_color"] = WHITE_TO_RED

        slider_b = Selector(**slider_kwargs)
        slider_b.callback = make_slider_callback(1, WHITE_TO_BLUE)
        slider_b.canvas["fg_color"] = WHITE_TO_BLUE

        slider_c = Selector(**slider_kwargs)
        slider_c.callback = lambda i: setattr(
            caster, "ambient_light", BLACK_TO_WHITE[i]
        )
        slider_c.canvas["fg_color"] = BLACK_TO_WHITE

        slider_d = Selector(**slider_kwargs)
        slider_d.callback = lambda i: setattr(caster, "radius", 10 + round(30 / 23 * i))
        slider_d.indicator.x = slider_d.width - 1

        label_a = Text(**label_kwargs)
        label_a.set_text("Light source A:")

        label_b = Text(**label_kwargs)
        label_b.set_text("Light source B:")

        label_c = Text(**label_kwargs)
        label_c.set_text("Ambient Light:")

        label_d = Text(**label_kwargs)
        label_d.set_text("Radius:")

        decay_label = Text(**label_kwargs)
        decay_label.set_text("Light Decay:")

        def make_decay_callback(i):
            decays = [
                lambda d: 1 if d == 0 else 1 / d,
                lambda d: math.exp(-0.1 * d),
                lambda d: 1 if d == 0 else math.sin(d) / d,
                lambda d: 1 if d == 0 else random.random() / d,
            ]

            def callback(state):
                if state == "on":
                    caster.light_decay = decays[i]

            return callback

        button_kwargs["group"] = 2
        button_d = ToggleButton(
            label="1 / d", callback=make_decay_callback(0), **button_kwargs
        )
        button_e = ToggleButton(
            label="exp(-0.1 * d)", callback=make_decay_callback(1), **button_kwargs
        )
        button_f = ToggleButton(
            label="sin(d) / d", callback=make_decay_callback(2), **button_kwargs
        )
        button_g = ToggleButton(
            label="random() / d", callback=make_decay_callback(3), **button_kwargs
        )

        grid_layout = GridLayout(
            grid_rows=17, grid_columns=1, pos=(0, caster.right + 1)
        )
        grid_layout.add_gadgets(
            button_label,
            button_a,
            button_b,
            button_c,
            label_a,
            slider_a,
            label_b,
            slider_b,
            label_c,
            slider_c,
            label_d,
            slider_d,
            decay_label,
            button_d,
            button_e,
            button_f,
            button_g,
        )
        grid_layout.size = grid_layout.min_grid_size

        container = Gadget(pos_hint={"y_hint": 0.5, "x_hint": 0.5}, size=(17, 58))
        container.add_gadgets(caster, grid_layout)
        self.add_gadget(container)

        theta = 0
        while True:
            for i in chain(range(21), range(21)[::-1]):
                # Move boxes
                caster_map[:] = 0
                caster_map[8:12, 5 + i : 5 + i + 4] = 1
                caster_map[22:26, 25 - i : 25 - i + 4] = 2
                # Move light sources
                theta = (theta + 0.1) % math.tau
                caster.light_coords[0] = (
                    18 * math.sin(theta) + 17,
                    18 * math.cos(theta) + 17,
                )
                caster.light_coords[1] = (
                    17 * math.cos(theta) + 17,
                    17 * math.sin(theta) + 17,
                )
                caster.cast_shadows()

                await asyncio.sleep(0.0166666)


if __name__ == "__main__":
    ShadowCasterApp(
        title="Shadow Casting",
        bg_color=NEPTUNE_PRIMARY_BG,
        inline=True,
        inline_height=17,
    ).run()
