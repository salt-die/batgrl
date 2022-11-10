from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.scroll_view import ScrollView
from nurses_2.widgets.window import Window
from nurses_2.widgets.text_widget import TextWidget


class MyApp(App):
    async def on_start(self):
        window = Window(title="Move/Resize Me")
        sv = ScrollView(allow_horizontal_scroll=False, show_horizontal_bar=False, show_vertical_bar=False)
        label = TextWidget(size=(2, 100), default_color_pair=DEFAULT_COLOR_THEME.primary_color_pair)

        label.subscribe(window, "pos", lambda: label.add_text(f"{window.pos}"))
        label.subscribe(window, "size", lambda: label.add_text(f"{window.size}", row=1))

        window.view = sv
        sv.view = label
        self.add_widget(window)
        window.size = 15, 30
        window.pos = 10, 10


MyApp(title="Subscribe Example").run()
