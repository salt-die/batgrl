"""
Button showcase.
"""
from batgrl.app import App
from batgrl.gadgets.button import Button
from batgrl.gadgets.flat_toggle import FlatToggle
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.text import Text
from batgrl.gadgets.toggle_button import ToggleButton, ToggleState


class ButtonApp(App):
    async def on_start(self):
        display = Text(size=(1, 20), pos=(1, 9))

        def button_callback(i):
            def callback():
                display.add_str(f"Button {i + 1} pressed!".ljust(20))

            return callback

        def toggle_button_callback(i):
            def callback(state):
                prefix = "un" if state is ToggleState.OFF else ""
                display.add_str(f"Button {i + 1} {prefix}toggled!".ljust(20))

            return callback

        grid_layout = GridLayout(
            grid_rows=5,
            grid_columns=3,
            pos=(2, 0),
            orientation="tb-lr",
            padding_left=1,
            padding_right=1,
            padding_top=1,
            padding_bottom=1,
            horizontal_spacing=1,
        )

        # Buttons
        grid_layout.add_gadgets(
            Button(size=(1, 10), label=f"Button {i + 1}", callback=button_callback(i))
            for i in range(5)
        )

        # Independent toggle buttons
        grid_layout.add_gadgets(
            ToggleButton(
                size=(1, 12),
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(5, 10)
        )

        # Grouped radio buttons
        grid_layout.add_gadgets(
            ToggleButton(
                size=(1, 12),
                group="a",
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(10, 15)
        )

        grid_layout.size = grid_layout.minimum_grid_size

        flat_grid = GridLayout(
            grid_rows=2,
            grid_columns=5,
            pos=(grid_layout.bottom, 7),
            orientation="lr-tb",
            horizontal_spacing=1,
        )

        # Independent flat toggles
        flat_grid.add_gadgets(
            FlatToggle(callback=toggle_button_callback(i)) for i in range(15, 20)
        )

        # Grouped flat toggles
        flat_grid.add_gadgets(
            FlatToggle(group="b", callback=toggle_button_callback(i))
            for i in range(20, 25)
        )

        flat_grid.size = flat_grid.minimum_grid_size

        self.add_gadgets(display, grid_layout, flat_grid)


if __name__ == "__main__":
    ButtonApp(title="Buttons Example").run()
