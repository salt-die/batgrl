"""Syntax highlighting example."""

import re
from pathlib import Path

from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG
from batgrl.gadgets.text_pad import TextPad

# Injection showcase: Comments and regex strings should be highlighted
# separately from python code!
BAT_RE = re.compile(r"(bat)\d+")  # TODO: Add additional tree-sitter queries!
GRL_RE = r"[grl]+bad|ass"  # FIXME: https://github.com/salt-die/batgrl


class SyntaxApp(App):
    async def on_start(self):
        code = Path(__file__).read_text()
        textpad = TextPad(
            size_hint={"height_hint": 1.0, "width_hint": 1.0},
            syntax_highlight_language="python",
        )
        textpad.text = code
        self.add_gadget(textpad)


if __name__ == "__main__":
    SyntaxApp(title="Syntax Highlighting Example", bg_color=NEPTUNE_PRIMARY_BG).run()
