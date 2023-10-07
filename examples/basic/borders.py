from batgrl.app import App
from batgrl.colors import BLACK, Color, ColorPair, rainbow_gradient
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.text import Border, Text

border_colors = [
    ColorPair.from_colors(fg, BLACK)
    for fg in rainbow_gradient(len(Border.__args__), color_type=Color)
]


class BordersApp(App):
    async def on_start(self):
        grid_layout = GridLayout(grid_columns=7, grid_rows=2)
        for border, color in zip(Border.__args__, border_colors):
            gadget = Text(size=(3, 17))
            gadget.add_border(border, bold=True, color_pair=color)
            gadget.add_str(f"{border:^15}", pos=(1, 1), italic=True)
            grid_layout.add_gadget(gadget)

        grid_layout.size = grid_layout.minimum_grid_size
        self.add_gadget(grid_layout)


if __name__ == "__main__":
    BordersApp(title="Borders").run()
