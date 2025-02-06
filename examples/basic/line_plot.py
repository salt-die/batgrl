import numpy as np
from batgrl.app import App
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.line_plot import LinePlot
from batgrl.gadgets.toggle_button import ToggleButton

XS = np.arange(20)
YS_1 = np.random.randint(0, 100, 20)
YS_2 = np.random.randint(0, 100, 20)
YS_3 = np.random.randint(0, 100, 20)


class PlotApp(App):
    async def on_start(self):
        BUTTON_WIDTH = 17

        plot = LinePlot(
            xs=[XS, XS, XS],
            ys=[YS_1, YS_2, YS_3],
            x_label="X Values",
            y_label="Y Values",
            legend_labels=["Before", "During", "After"],
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            blitter="braille",
        )

        def set_braille_mode(toggle_state):
            if toggle_state == "on":
                plot.blitter = "braille"

        def set_half_mode(toggle_state):
            if toggle_state == "on":
                plot.blitter = "half"

        def set_sixel_mode(toggle_state):
            if toggle_state == "on":
                plot.blitter = "sixel"

        braille_button = ToggleButton(
            size=(1, BUTTON_WIDTH),
            label="Braille Blitter",
            callback=set_braille_mode,
            group=0,
        )
        half_button = ToggleButton(
            size=(1, BUTTON_WIDTH),
            pos=(1, 0),
            label="Half Blitter",
            callback=set_half_mode,
            group=0,
        )
        sixel_button = ToggleButton(
            size=(1, BUTTON_WIDTH),
            pos=(2, 0),
            label="Sixel Blitter",
            callback=set_sixel_mode,
            group=0,
        )

        container = Gadget(
            size=(3, BUTTON_WIDTH), pos_hint={"x_hint": 1.0, "anchor": "top-right"}
        )
        container.add_gadgets(braille_button, half_button, sixel_button)
        self.add_gadgets(plot, container)


if __name__ == "__main__":
    PlotApp(title="Line Plot Example").run()
