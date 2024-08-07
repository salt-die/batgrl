"""Example slider gadget."""

from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.slider import Slider
from batgrl.gadgets.text import Text, new_cell


class SliderApp(App):
    async def on_start(self):
        display = Text(
            size=(3, 30),
            default_cell=new_cell(
                fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            ),
        )
        slider_1 = Slider(
            size=(1, 20),
            pos=(1, 0),
            min=0,
            max=100,
            callback=lambda value: display.add_str(
                f"{round(value, 3):<10}", pos=(0, 7)
            ),
            bg_color=DEFAULT_PRIMARY_BG,
        )
        slider_2 = Slider(
            size=(3, 16),
            pos=(3, 2),
            min=-20,
            max=50,
            callback=lambda value: display.add_str(
                f"{round(value, 3):<10}", pos=(2, 7)
            ),
            bg_color=(55, 55, 55),
            fill_color=(220, 120, 0),
        )
        self.add_gadgets(display, slider_1, slider_2)


if __name__ == "__main__":
    SliderApp(title="Slider Example", bg_color=DEFAULT_PRIMARY_BG).run()
