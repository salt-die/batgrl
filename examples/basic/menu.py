from nurses_2.app import App
from nurses_2.widgets.menu import MenuBar
from nurses_2.widgets.text_widget import TextWidget


class MenuApp(App):
    async def on_start(self):
        label = TextWidget(size=(1, 50))

        def add_label(text):
            def inner():
                label.add_str(f"{text:<50}"[:50])

            return inner

        def add_label_toggle(text):
            def inner(toggle_state):
                label.add_str(f"{f'{text} {toggle_state}':<50}"[:50])

            return inner

        # These "keybinds" aren't implemented.
        file_menu = {
            ("New File", "Ctrl+N"): add_label("New File"),
            ("Open File...", "Ctrl+O"): add_label("Open File..."),
            ("Save", "Ctrl+S"): add_label("Save"),
            ("Save as...", "Ctrl+Shift+S"): add_label("Save as..."),
            ("Preferences", ""): {
                ("Settings", "Ctrl+,"): add_label("Settings"),
                ("Keyboard Shortcuts", "Ctrl+K Ctrl+S"): add_label(
                    "Keyboard Shortcuts"
                ),
                ("Toggle Item 1", ""): add_label_toggle("Toggle Item 1"),
                ("Toggle Item 2", ""): add_label_toggle("Toggle Item 2"),
            },
        }

        edit_menu = {
            ("Undo", "Ctrl+Z"): add_label("Undo"),
            ("Redo", "Ctrl+Y"): add_label("Redo"),
            ("Cut", "Ctrl+X"): add_label("Cut"),
            ("Copy", "Ctrl+C"): add_label("Copy"),
            ("Paste", "Ctrl+V"): add_label("Paste"),
        }

        self.add_widget(label)
        self.add_widgets(
            MenuBar.from_iterable(
                (("File", file_menu), ("Edit", edit_menu)), pos=(2, 0)
            )
        )

        self.children[-2].children[1].item_disabled = True


if __name__ == "__main__":
    MenuApp(title="Menu Example").run()
