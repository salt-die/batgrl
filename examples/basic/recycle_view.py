from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG, NEPTUNE_PRIMARY_FG
from batgrl.gadgets.gadget import Point, Size
from batgrl.gadgets.recycle_view import RecycleView
from batgrl.gadgets.text import Text, new_cell

DEFAULT_CELL = new_cell(fg_color=NEPTUNE_PRIMARY_FG, bg_color=NEPTUNE_PRIMARY_BG)


class MyRecycleView(RecycleView):
    def new_data_view(self) -> Text:
        return Text(default_cell=DEFAULT_CELL)

    def update_data_view(self, data_view: Text, text: str) -> None:
        data_view.clear()
        data_view.add_border()
        data_view.add_str(text, pos=(1, 1))

    def get_layout(self, i: int) -> tuple[Size, Point]:
        return Size(3, 36), Point(3 * i, 0)


class RecycleApp(App):
    async def on_start(self):
        recycle_view = MyRecycleView(
            recycle_view_data=[
                f"This is a view of the {i:03d}th datum." for i in range(1000)
            ],
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            dynamic_bars=True,
        )
        label = Text(pos_hint={"x_hint": 1.0, "x_offset": -2, "anchor": "right"})

        def update_label():
            label.set_text(
                f"RecycleView data has {len(recycle_view.recycle_view_data)} items,\n"
                f"but only {len(recycle_view.view.children)} data-view gadget children."
            )

        update_label()
        recycle_view.view.bind("pos", update_label)
        self.add_gadgets(recycle_view, label)


if __name__ == "__main__":
    RecycleApp(title="Recycle-view example.").run()
