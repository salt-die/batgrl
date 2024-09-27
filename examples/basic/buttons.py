"""Button showcase."""

from batgrl.app import App
from batgrl.gadgets.button import Button
from batgrl.gadgets.flat_toggle import FlatToggle
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.text import Text
from batgrl.gadgets.toggle_button import ToggleButton


class ButtonApp(App):
    async def on_start(self):
        display = Text(size=(1, 20), pos_hint={"x_hint": 0.5}, is_transparent=True)

        def button_callback(i):
            def callback():
                display.add_str(f"Button {i + 1} pressed!".center(20))

            return callback

        def toggle_button_callback(i):
            def callback(state):
                prefix = "un" if state == "off" else ""
                display.add_str(f"Button {i + 1} {prefix}toggled!".center(20))

            return callback

        grid_layout = GridLayout(
            grid_rows=5,
            grid_columns=3,
            pos=(1, 0),
            orientation="tb-lr",
            padding_left=1,
            padding_right=1,
            padding_top=1,
            padding_bottom=1,
            horizontal_spacing=1,
        )

        grid_layout.add_gadgets(
            Button(size=(1, 10), label=f"Button {i + 1}", callback=button_callback(i))
            for i in range(5)
        )
        grid_layout.children[-1].button_state = "disallowed"
        grid_layout.add_gadgets(
            ToggleButton(
                size=(1, 12),
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(5, 10)
        )
        grid_layout.children[-1].button_state = "disallowed"
        grid_layout.add_gadgets(
            ToggleButton(
                size=(1, 12),
                group=0,
                label=f"Button {i + 1}",
                callback=toggle_button_callback(i),
            )
            for i in range(10, 15)
        )
        grid_layout.children[-1].button_state = "disallowed"
        grid_layout.size = grid_layout.min_grid_size

        flat_grid = GridLayout(
            grid_rows=2,
            grid_columns=5,
            pos=(grid_layout.bottom, 0),
            pos_hint={"x_hint": 0.5},
            orientation="lr-tb",
            horizontal_spacing=1,
            vertical_spacing=1,
        )
        flat_grid.add_gadgets(
            FlatToggle(size=(1, 3), callback=toggle_button_callback(i))
            for i in range(15, 20)
        )
        flat_grid.children[-1].toggle_state = "on"
        flat_grid.children[-1].button_state = "disallowed"
        flat_grid.add_gadgets(
            FlatToggle(size=(1, 3), group=1, callback=toggle_button_callback(i))
            for i in range(20, 25)
        )
        flat_grid.children[-1].button_state = "disallowed"
        flat_grid.size = flat_grid.min_grid_size
        container = Gadget(pos_hint={"x_hint": 0.5})
        container.add_gadgets(display, grid_layout, flat_grid)
        container.width = grid_layout.width
        container.height = flat_grid.bottom
        self.add_gadget(container)


if __name__ == "__main__":
    ButtonApp(title="Buttons Example", inline=True, inline_height=11).run()
