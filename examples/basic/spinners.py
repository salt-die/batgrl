from math import ceil

from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG, NEPTUNE_PRIMARY_FG
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.text_animation import TextAnimation
from batgrl.spinners import SPINNERS

COLUMNS = 2


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
            is_transparent=True,
        )
        default_cell = new_cell(
            fg_color=NEPTUNE_PRIMARY_FG, bg_color=NEPTUNE_PRIMARY_BG
        )

        for name, frames in SPINNERS.items():
            label = Text(
                pos_hint={"y_hint": 0.5, "anchor": "left"},
                default_cell=default_cell,
            )
            label.set_text(f"{name}: ")

            animation = TextAnimation(
                pos=(0, label.right), frames=frames, default_cell=default_cell
            )
            animation.size = animation.min_animation_size
            animation.play()

            container = Gadget(
                size=(animation.height, label.width + animation.width),
                is_transparent=True,
            )
            container.add_gadgets(label, animation)

            grid.add_gadget(container)

        grid.size = grid.min_grid_size
        sv.view = grid
        self.add_gadget(sv)


if __name__ == "__main__":
    SpinnersApp(title="Spinners").run()
