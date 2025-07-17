"""Syntax highlighting example."""

from pathlib import Path

from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text


class SyntaxApp(App):
    async def on_start(self):
        code = Path(__file__).read_text()
        text = Text()
        text.set_text(code)
        text.add_syntax_highlighting("python")

        sv = ScrollView(
            pos=(2, 0),
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            dynamic_bars=True,
        )
        sv.view = text

        self.add_gadget(sv)


if __name__ == "__main__":
    SyntaxApp(title="Syntax Highlighting Example", bg_color=NEPTUNE_PRIMARY_BG).run()
