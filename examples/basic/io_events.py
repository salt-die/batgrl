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

    def on_keypress(self, key_press_event: KeyPressEvent) -> bool | None:
        self._on_io(key_press_event)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self._on_io(mouse_event)

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        self._on_io(paste_event)

    def _on_io(self, event):
        self.canvas[:] = " "

        match event:
            case KeyPressEvent():
                text = dedent(f"""
                Got keypress event:
                    key: {event.key}
                    mods: {event.mods}
                """)
            case MouseEvent():
                text = dedent(f"""
                Got mouse event:
                    position: {event.position}
                    type: {event.event_type}
                    button: {event.button}
                    nclicks: {event.nclicks}
                    mods: {event.mods}
                """)
            case PasteEvent():
                text = "Got paste event:\n" + event.paste

        for i, line in enumerate(text.splitlines()):
            self.add_text(self._just(line), row=i)

    def _just(self, text):
        """
        Adjust text to be exactly width of widget.
        """
        return text.ljust(self.width)[:self.width]

run_widget_as_app(ShowIOEvents, size_hint=(1.0, 1.0))
