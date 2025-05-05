import numpy as np
from batgrl.app import App
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.line_plot import Blitter, LinePlot
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

        def set_mode(mode):
            def inner(toggle_state):
                if toggle_state == "on":
                    plot.blitter = mode

            return inner

        buttons = [
            ToggleButton(
                size=(1, BUTTON_WIDTH),
                pos=(i, 0),
                label=f"{blitter.capitalize()} Blitter",
                callback=set_mode(blitter),
                group=0,
            )
            for i, blitter in enumerate(Blitter.__args__)
        ]

        container = Gadget(
            size=(len(buttons), BUTTON_WIDTH),
            pos_hint={"x_hint": 1.0, "anchor": "top-right"},
        )
        container.add_gadgets(buttons)
        self.add_gadgets(plot, container)


if __name__ == "__main__":
    PlotApp(title="Line Plot Example").run()
