"""
Move/click mouse, press keys or paste in terminal to show IO events.
"""
from textwrap import dedent

from nurses_2.app import run_widget_as_app
from nurses_2.io import KeyPressEvent, MouseEvent, PasteEvent
from nurses_2.widgets.text_widget import TextWidget


class ShowIOEvents(TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_key_press(self, key_press_event: KeyPressEvent) -> bool | None:
        self._on_io(key_press_event)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self._on_io(mouse_event)

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        self._on_io(paste_event)

    def _on_io(self, event):
        self.canvas[:] = " "

        match event:
            case KeyPressEvent():
                text = """
                Got key_press event:
                    key: {}
                    mods: {}
                """
            case MouseEvent():
                text = """
                Got mouse event:
                    position: {}
                    type: {}
                    button: {}
                    mods: {}
                    nclicks: {}
                """
            case PasteEvent():
                text = "\nGot paste event:\n{}"

        lines = dedent(text.format(*event)).splitlines()
        for i, line in enumerate(lines):
            self.add_text(line.ljust(self.width)[:self.width], row=i)


run_widget_as_app(ShowIOEvents(size_hint=(1.0, 1.0)))
