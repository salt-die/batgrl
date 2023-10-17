"""
A syntax highlighting example with `pygments`.

Requires `pygments>=2.14`.

`add_syntax_highlighting` may be included in `batgrl` in the future.
"""
from pathlib import Path

from pygments.lexer import Lexer
from pygments.lexers import get_lexer_by_name
from pygments.style import Style
from pygments.styles import get_style_by_name
from wcwidth import wcswidth

from batgrl.app import App
from batgrl.colors import Color
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text


def add_syntax_highlighting(text_gadget: Text, lexer: Lexer, style: Style):
    """
    Add syntax highlighting to a text gadget.

    Parameters
    ----------
    text_gadget : Text
        The gadget to be highlighted.

    lexer : Lexer
        A pygments `Lexer` object.

    style : Style
        A pygments `Style` object.
    """
    y = x = 0
    canvas = text_gadget.canvas
    colors = text_gadget.colors

    colors[..., 3:] = Color.from_hex(style.background_color)

    text = "\n".join("".join(line).rstrip() for line in canvas["char"])
    for ttype, value in lexer.get_tokens(text):
        lines = value.split("\n")
        token_style = style.style_for_token(ttype)

        for i, line in enumerate(lines):
            if i > 0:
                y += 1
                x = 0
            end = x + wcswidth(line)
            if token_style["color"]:
                colors[y, x:end, :3] = Color.from_hex(token_style["color"])
            if token_style["bgcolor"]:
                colors[y, x:end, 3:] = Color.from_hex(token_style["bgcolor"])
            canvas[y, x:end]["bold"] = token_style["bold"]
            canvas[y, x:end]["italic"] = token_style["italic"]
            canvas[y, x:end]["underline"] = token_style["underline"]
            x = end


PYTHON_LEXER = get_lexer_by_name("Python")
STYLE = get_style_by_name("github-dark")


class SyntaxApp(App):
    async def on_start(self):
        code = Path(__file__).read_text()
        text = Text()
        text.set_text(code)
        add_syntax_highlighting(text, PYTHON_LEXER, STYLE)
        sv = ScrollView(
            size=(1, text.width + 2),
            size_hint={"height_hint": 1.0},
            show_horizontal_bar=False,
        )
        sv.view = text
        self.add_gadget(sv)


if __name__ == "__main__":
    SyntaxApp(title="Syntax Highlighting Example").run()
