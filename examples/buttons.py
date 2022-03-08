import asyncio

from nurses_2.app import App
from nurses_2.widgets.button import Button
from nurses_2.widgets.grid_layout import GridLayout
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.toggle_button import ToggleButton, ToggleState


class MyApp(App):
    async def on_start(self):
        display = TextWidget(size=(1, 20), pos=(1, 9))
        display._clear_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

        async def clear_display():
            await asyncio.sleep(3)
            display.canvas[:] = " "

        def button_callback(i):
            def callback():
                display.add_text(f"Button {i + 1} pressed!".ljust(20))
                display._clear_task.cancel()
                display._clear_task = asyncio.create_task(clear_display())

            return callback

        def toggle_button_callback(i):
            def callback(state):
                display.add_text(f"Button {i + 1} {'un' if state is ToggleState.OFF else ''}toggled!".ljust(20))
                display._clear_task.cancel()
                display._clear_task = asyncio.create_task(clear_display())

            return callback

        grid_layout = GridLayout(5, 3, pos=(2, 0), size=(5, 36))

        # Buttons
        buttons = [
            Button(label=f"Button {i + 1}", callback=button_callback(i))
            for i in range(5)
        ]

        # Independent toggle buttons
        toggles = [
            ToggleButton(label=f"Button {i + 1}", callback=toggle_button_callback(i))
            for i in range(5, 10)
        ]

        # Grouped radio buttons
        radios = [
            ToggleButton(
                group="my_group",
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(10, 15)
        ]

        for button, toggle, radio in zip(buttons, toggles, radios):
            grid_layout.add_widgets(button, toggle, radio)

        self.add_widgets(display, grid_layout)


MyApp().run()
