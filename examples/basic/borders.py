from batgrl.app import App
from batgrl.colors import rainbow_gradient
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.text import Border, Text

border_colors = rainbow_gradient(len(Border.__args__))


class BordersApp(App):
    async def on_start(self):
        grid_layout = GridLayout(grid_columns=6, grid_rows=3)
        for border, color in zip(Border.__args__, border_colors):
            gadget = Text(size=(3, 17))
            gadget.add_border(border, fg_color=color)
            gadget.add_str(f"{f'*{border}*':^17}", pos=(1, 1), markdown=True)
            grid_layout.add_gadget(gadget)

        grid_layout.size = grid_layout.minimum_grid_size
        self.add_gadget(grid_layout)


if __name__ == "__main__":
    BordersApp(title="Borders").run()
