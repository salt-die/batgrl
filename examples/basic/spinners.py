from math import ceil

from nurses_2.app import App
from nurses_2.spinners import SPINNERS
from nurses_2.widgets.grid_layout import GridLayout
from nurses_2.widgets.scroll_view import ScrollView
from nurses_2.widgets.text_animation import TextAnimation
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

COLUMNS = 2


class SpinnersApp(App):
    async def on_start(self):
        sv = ScrollView(
            size_hint=(1.0, 1.0),
            allow_horizontal_scroll=False,
            show_horizontal_bar=False,
        )
        grid = GridLayout(
            grid_rows=ceil(len(SPINNERS) / COLUMNS),
            grid_columns=COLUMNS,
            horizontal_spacing=1,
            orientation="tb-lr",
        )

        for name, frames in SPINNERS.items():
            label = TextWidget(pos_hint=(.5, None), anchor="left_center")
            label.set_text(f"{name}: ")

            animation = TextAnimation(pos=(0, label.right), frames=frames)
            animation.size = animation.frames[0].size
            animation.play()

            container = Widget(size=(animation.height, label.width + animation.width))
            container.add_widgets(label, animation)

            grid.add_widget(container)

        grid.size = grid.minimum_grid_size
        sv.view = grid
        self.add_widget(sv)


SpinnersApp(title="Spinners").run()
