from nurses_2.app import App
from nurses_2.colors import rainbow_gradient, Color, ColorPair, BLACK
from nurses_2.widgets.text_widget import TextWidget, Border

border_colors = [
    ColorPair.from_colors(fg, BLACK)
    for fg in rainbow_gradient(len(Border), color_type=Color)
]


class BordersApp(App):
    async def on_start(self):
        for i, border in enumerate(Border):
            widget = TextWidget(size=(3, 17), pos=(i * 3, 0))
            widget.add_border(border, color_pair=border_colors[i])
            widget.add_str(f"{border:^15}", pos=(1, 1), italic=True)
            self.add_widget(widget)

        return await super().on_start()


BordersApp(title="Borders").run()
