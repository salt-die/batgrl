from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.text import Text, style_char
from batgrl.gadgets.window import Window


class SubscriptionApp(App):
    async def on_start(self):
        window = Window(title="Move/Resize Me")
        label = Text(
            size=(2, 100),
            default_cell=style_char(
                fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            ),
        )

        label.subscribe(
            window,
            "pos",
            lambda: label.add_str(f"{window.pos}".ljust(30), truncate_str=True)
            if label.height > 0
            else None,
        )
        label.subscribe(
            window,
            "size",
            lambda: label.add_str(
                f"{window.size}".ljust(30), pos=(1, 0), truncate_str=True
            )
            if label.height > 1
            else None,
        )

        window.view = label
        self.add_gadget(window)
        window.size = 15, 30
        window.pos = 10, 10


if __name__ == "__main__":
    SubscriptionApp(title="Subscribe Example").run()
