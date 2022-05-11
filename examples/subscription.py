from nurses_2.app import App
from nurses_2.widgets.window import Window
from nurses_2.widgets.text_widget import TextWidget


class MyApp(App):
    async def on_start(self):
        window = Window()

        label = TextWidget(size=(2, 100))

        label.subscribe(window, "pos", lambda: label.add_text(f"{window.pos}"))
        label.subscribe(window, "size", lambda: label.add_text(f"{window.size}", row=1))

        window.add_widget(label)
        self.add_widget(window)


MyApp(title="Widget Events Example").run()
