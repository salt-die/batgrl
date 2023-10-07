from batgrl.app import App
from batgrl.colors import DEFAULT_COLOR_THEME
from batgrl.gadgets.text import Text
from batgrl.gadgets.window import Window


class SubscriptionApp(App):
    async def on_start(self):
        window = Window(title="Move/Resize Me")
        label = Text(size=(2, 100), default_color_pair=DEFAULT_COLOR_THEME.primary)

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
            lambda: label.add_str(f"{window.size}".ljust(30), (1, 0), truncate_str=True)
            if label.height > 1
            else None,
        )

        window.view = label
        self.add_gadget(window)
        window.size = 15, 30
        window.pos = 10, 10


if __name__ == "__main__":
    SubscriptionApp(title="Subscribe Example").run()
