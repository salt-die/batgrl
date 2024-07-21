"""Move/click mouse, press keys, paste, or gain/lose focus to show IO events."""

from dataclasses import fields

from batgrl.app import App
from batgrl.gadgets.text import Text
from batgrl.gadgets.text_tools import add_text
from batgrl.terminal.events import FocusEvent, KeyEvent, MouseEvent, PasteEvent


class ShowIOEvents(Text):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_key(self, key_event: KeyEvent) -> bool | None:
        self._on_io(key_event)

    def on_mouse(self, mouse_event: MouseEvent) -> bool | None:
        self._on_io(mouse_event)

    def on_paste(self, paste_event: PasteEvent) -> bool | None:
        self.clear()
        add_text(self.canvas, "PasteEvent:\n" + paste_event.paste, truncate_text=True)

    def on_terminal_focus(self, focus_event: FocusEvent) -> bool | None:
        self._on_io(focus_event)

    def _on_io(self, event):
        self.clear()
        event_repr = str(event)
        if len(event_repr) <= self.width:
            self.add_str(event_repr)
        else:
            fields_repr = "".join(
                f"    {field.name}={getattr(event, field.name)!r},\n"
                for field in fields(event)
            )
            full_repr = f"{type(event).__name__}(\n{fields_repr})"
            add_text(self.canvas, full_repr, truncate_text=True)


class IoApp(App):
    async def on_start(self):
        events = ShowIOEvents(size_hint={"height_hint": 1.0, "width_hint": 1.0})
        self.add_gadget(events)


if __name__ == "__main__":
    IoApp().run()
