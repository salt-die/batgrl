from nurses_2.app import App
from nurses_2.colors import BLACK, Color, ColorPair, rainbow_gradient
from nurses_2.widgets.grid_layout import GridLayout
from nurses_2.widgets.text import Border, Text

border_colors = [
    ColorPair.from_colors(fg, BLACK)
    for fg in rainbow_gradient(len(Border.__args__), color_type=Color)
]


class BordersApp(App):
    async def on_start(self):
        grid_layout = GridLayout(grid_columns=7, grid_rows=2)
        for border, color in zip(Border.__args__, border_colors):
            widget = Text(size=(3, 17))
            widget.add_border(border, bold=True, color_pair=color)
            widget.add_str(f"{border:^15}", pos=(1, 1), italic=True)
            grid_layout.add_widget(widget)

        grid_layout.size = grid_layout.minimum_grid_size
        self.add_widget(grid_layout)


if __name__ == "__main__":
    BordersApp(title="Borders").run()
