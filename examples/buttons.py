from nurses_2.app import App
from nurses_2.widgets.button import Button


class MyApp(App):
    async def on_start(self):
        self.add_widgets(
            Button(
                label=f"Button {i + 1}",
                callback=lambda: None,
                size=(3, 10),
                pos=(3 * i, 0),
            )
            for i in range(5)
        )


MyApp().run()
