import asyncio
from math import ceil
from time import perf_counter

from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.text_animation import TextAnimation
from batgrl.spinners import SPINNERS

COLUMNS = 2


class FPSTracker(Text):
    """A gadget that displays frames per second."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._rolling_average: float = 0
        self._nmeasures: int = 0

    def on_add(self):
        super().on_add()
        self._fps_task = asyncio.create_task(self._fps_tracker())

    def on_remove(self):
        self._fps_task.cancel()
        super().on_remove()

    async def _fps_tracker(self):
        last_time = perf_counter()
        while True:
            current_time = perf_counter()
            elapsed_time = current_time - last_time
            last_time = current_time

            if elapsed_time != 0:
                self._rolling_average += elapsed_time
                self._nmeasures += 1
                self.set_text(f"{self._nmeasures / self._rolling_average:0.3f} fps")

            await asyncio.sleep(0)


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
        fps = FPSTracker()

        for name, frames in SPINNERS.items():
            label = Text(
                pos_hint={"y_hint": 0.5, "anchor": "left"},
                default_cell=new_cell(
                    fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
                ),
            )
            label.set_text(f"{name}: ")

            animation = TextAnimation(
                pos=(0, label.right),
                frames=frames,
                animation_fg_color=DEFAULT_PRIMARY_FG,
                animation_bg_color=DEFAULT_PRIMARY_BG,
            )
            animation.size = animation.frames[0].size
            animation.play()

            container = Gadget(
                size=(animation.height, label.width + animation.width),
                is_transparent=True,
            )
            container.add_gadgets(label, animation)

            grid.add_gadget(container)

        grid.size = grid.min_grid_size
        sv.view = grid
        self.add_gadgets(sv, fps)
        await asyncio.sleep(5)


if __name__ == "__main__":
    SpinnersApp(title="Spinners").run()
