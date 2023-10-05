from math import ceil

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.spinners import SPINNERS
from nurses_2.widgets.grid_layout import GridLayout
from nurses_2.widgets.scroll_view import ScrollView
from nurses_2.widgets.text import Text
from nurses_2.widgets.text_animation import TextAnimation
from nurses_2.widgets.widget import Widget

COLUMNS = 2
PRIMARY = DEFAULT_COLOR_THEME.primary


class SpinnersApp(App):
    async def on_start(self):
        sv = ScrollView(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            allow_horizontal_scroll=False,
            show_horizontal_bar=False,
            background_color_pair=PRIMARY,
        )
        grid = GridLayout(
            grid_rows=ceil(len(SPINNERS) / COLUMNS),
            grid_columns=COLUMNS,
            horizontal_spacing=1,
            orientation="tb-lr",
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

            container = Widget(size=(animation.height, label.width + animation.width))
            container.add_widgets(label, animation)

            grid.add_widget(container)

        grid.size = grid.minimum_grid_size
        sv.view = grid
        self.add_widget(sv)


if __name__ == "__main__":
    SpinnersApp(title="Spinners").run()
