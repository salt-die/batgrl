import asyncio

from nurses_2.app import App
from nurses_2.widgets.button import Button
from nurses_2.widgets.grid_layout import GridLayout, Orientation
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.toggle_button import ToggleButton, ToggleState


class MyApp(App):
    async def on_start(self):
        display = TextWidget(size=(1, 20), pos=(1, 9))

        def button_callback(i):
            def callback():
                display.add_text(f"Button {i + 1} pressed!".ljust(20))
            return callback

        def toggle_button_callback(i):
            def callback(state):
                display.add_text(f"Button {i + 1} {'un' if state is ToggleState.OFF else ''}toggled!".ljust(20))
            return callback

        grid_layout = GridLayout(
            grid_rows=5,
            grid_columns=3,
            pos=(2, 0),
            orientation=Orientation.BT_LR,
            top_padding=1,
            bottom_padding=1,
            left_padding=1,
            right_padding=1,
            horizontal_spacing=1,
        )

        # Buttons
        grid_layout.add_widgets(
            Button(size=(1, 10), label=f"Button {i + 1}", callback=button_callback(i))
            for i in range(5)
        )

        # Independent toggle buttons
        grid_layout.add_widgets(
            ToggleButton(size=(1, 12), label=f"Button {i + 1}", callback=toggle_button_callback(i))
            for i in range(5, 10)
        )

        # Grouped radio buttons
        grid_layout.add_widgets(
            ToggleButton(
                size=(1, 12),
                group="my_group",
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(10, 15)
        )

        grid_layout.size = grid_layout.minimum_grid_size

        self.add_widgets(display, grid_layout)


MyApp(title="Buttons Example").run()
