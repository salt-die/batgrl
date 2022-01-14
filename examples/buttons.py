from nurses_2.app import App
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.button import Button


class MyApp(App):
    async def on_start(self):
        display = TextWidget(size=(1, 20), pos=(7, 15))
        self.add_widget(display)

        self.add_widgets(
            Button(
                label=f"Button {i + 1}",
                callback=lambda text=f"Button {i + 1} pressed!": display.add_text(text),
                size=(3, 10),
                pos=(3 * i, 0),
            )
            for i in range(5)
        )


MyApp().run()
