from nurses_2.app import App
from nurses_2.widgets.button import Button
from nurses_2.widgets.menu import Menu
from nurses_2.widgets.text_widget import TextWidget

class MyApp(App):
    async def on_start(self):
        label = TextWidget(size=(1, 50))

        def add_text(text):
            def inner():
                label.add_text(f"{text:<50}"[:50])
            return inner

        # These "keybinds" aren't implemented.
        menu_dict = {
            ("New File", "Ctrl+N"): add_text("New File"),
            ("Open File...", "Ctrl+O"): add_text("Open File..."),
            ("Save", "Ctrl+S"): add_text("Save"),
            ("Save as...", "Ctrl+Shift+S"): add_text("Save as..."),
            ("Preferences", ""): {
                ("Settings", "Ctrl+,"): add_text("Settings"),
                ("Keyboard Shortcuts", "Ctrl+K Ctrl+S"): add_text("Keyboard Shortcuts"),
            },
        }

        self.add_widget(label)
        self.add_widgets(Menu.from_dict_of_dicts(menu_dict, pos=(2, 0)))

        root_menu = self.children[-1]
        root_menu.is_enabled = False
        root_menu.children[1].item_disabled = True

        def toggle_root_menu():
            root_menu.is_enabled = not root_menu.is_enabled

        self.add_widget(Button(label="File", callback=toggle_root_menu, pos=(1, 0), size=(1, 6)))


MyApp().run()
