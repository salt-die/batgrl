from batgrl.app import App
from batgrl.gadgets.console import Console


class ConsoleApp(App):
    async def on_start(self):
        console = Console(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self.add_gadget(console)


if __name__ == "__main__":
    ConsoleApp(title="batgrl Console").run()
