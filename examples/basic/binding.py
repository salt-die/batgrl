"""
An example to showcase binding.

After binding a callback to gadget property, the callback will be called anytime the
property is updated.
"""

from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG, NEPTUNE_PRIMARY_FG
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.window import Window


class BindingApp(App):
    async def on_start(self):
        window = Window(title="Move/Resize Me")
        label = Text(
            default_cell=new_cell(
                fg_color=NEPTUNE_PRIMARY_FG, bg_color=NEPTUNE_PRIMARY_BG
            ),
        )

        def update_label():
            if label.height > 0:
                label.add_str(f"{window.pos}".ljust(30), truncate_str=True)
            if label.height > 1:
                label.add_str(f"{window.size}".ljust(30), pos=(1, 0), truncate_str=True)

        window.bind("pos", update_label)
        window.bind("size", update_label)

        window.view = label
        self.add_gadget(window)
        window.size = 15, 30
        window.pos = 10, 10


if __name__ == "__main__":
    BindingApp(title="Binding Example").run()
