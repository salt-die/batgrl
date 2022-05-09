from nurses_2.app import App
from nurses_2.widgets.window import Window
from nurses_2.widgets.text_widget import TextWidget


class MyApp(App):
    async def on_start(self):
        window = Window()

        label = TextWidget(size=(4, 100))

        def report(event, i):
            label.add_text(f"{event}", row=i)
            label.add_text(f"{getattr(event.source, event.attr)}", row=i + 1)

        label.subscribe(window, "pos", report, 0)
        label.subscribe(window, "size", report, 2)

        window.add_widget(label)
        self.add_widget(window)


MyApp().run()
