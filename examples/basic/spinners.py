from math import ceil

from batgrl.app import App
from batgrl.colors import DEFAULT_COLOR_THEME
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text
from batgrl.gadgets.text_animation import TextAnimation
from batgrl.spinners import SPINNERS

COLUMNS = 2
PRIMARY = DEFAULT_COLOR_THEME.primary


class SpinnersApp(App):
    async def on_start(self):
        sv = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            allow_horizontal_scroll=False,
            show_horizontal_bar=False,
        )
        grid = GridLayout(
            grid_rows=ceil(len(SPINNERS) / COLUMNS),
            grid_columns=COLUMNS,
            horizontal_spacing=1,
            orientation="tb-lr",
            background_color_pair=PRIMARY,
        )

        for name, frames in SPINNERS.items():
            label = Text(
                pos_hint={"y_hint": 0.5, "anchor": "left"}, default_color_pair=PRIMARY
            )
            label.set_text(f"{name}: ")

            animation = TextAnimation(
                pos=(0, label.right), frames=frames, animation_color_pair=PRIMARY
            )
            animation.size = animation.frames[0].size
            animation.play()

            container = Gadget(
                size=(animation.height, label.width + animation.width),
                is_transparent=True,
            )
            container.add_gadgets(label, animation)

            grid.add_gadget(container)

        grid.size = grid.minimum_grid_size
        sv.view = grid
        self.add_gadget(sv)


if __name__ == "__main__":
    SpinnersApp(title="Spinners", render_mode="painter").run()
