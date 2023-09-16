from nurses_2.app import App
from nurses_2.colors import BLACK, Color, ColorPair, rainbow_gradient
from nurses_2.widgets.text_widget import Border, TextWidget

border_colors = [
    ColorPair.from_colors(fg, BLACK)
    for fg in rainbow_gradient(len(Border.__args__), color_type=Color)
]


class BordersApp(App):
    async def on_start(self):
        for i, border in enumerate(Border.__args__):
            widget = TextWidget(size=(3, 17), pos=(i * 3, 0))
            widget.add_border(border, color_pair=border_colors[i])
            widget.add_str(f"{border:^15}", pos=(1, 1), italic=True)
            self.add_widget(widget)

        return await super().on_start()


BordersApp(title="Borders").run()
