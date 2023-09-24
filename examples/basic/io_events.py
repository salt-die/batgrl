"""
Move/click mouse, press keys or paste in terminal to show IO events.
"""
from textwrap import dedent

from nurses_2.app import run_widget_as_app
from nurses_2.io import KeyEvent, MouseEvent, PasteEvent
from nurses_2.widgets.text_widget import TextWidget


class ShowIOEvents(TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_key(self, key_event: KeyEvent) -> bool | None:
        self._on_io(key_event)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self._on_io(mouse_event)

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        self._on_io(paste_event)

    def _on_io(self, event):
        self.canvas["char"][:] = " "

        match event:
            case KeyEvent():
                text = """
                Got key event:
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
            self.add_str(line.ljust(self.width)[: self.width], (i, 0))


if __name__ == "__main__":
    run_widget_as_app(ShowIOEvents(size_hint=(1.0, 1.0)))
