"""
A syntax highlighting example with `pygments`.

Requires `pygments>=2.14`.

`add_syntax_highlighting` may be included in `nurses_2` in the future.
"""
from wcwidth import wcswidth

from pygments.lexer import Lexer
from pygments.style import Style
from pygments.lexers import get_lexer_by_name
from pygments.styles import get_style_by_name

from nurses_2.app import App
from nurses_2.colors import Color
from nurses_2.widgets.text_widget import TextWidget

def add_syntax_highlighting(text_widget: TextWidget, lexer: Lexer, style: Style):
    """
    Add syntax highlighting to a text widget.

    Parameters
    ----------
    text_widget : TextWidget
        The widget to be highlighted.

    lexer : Lexer
        A pygments `Lexer` object.

    style : Style
        A pygments `Style` object.
    """
    y = x = 0
    canvas = text_widget.canvas
    colors = text_widget.colors

    colors[..., 3:] = Color.from_hex(style.background_color)

    text = "\n".join("".join(line).rstrip() for line in canvas["char"])
    for ttype, value in lexer.get_tokens(text):
        if value == "\n":
            y += 1
            x = 0
            continue

        token_style = style.style_for_token(ttype)
        end = x + wcswidth(value)
        if token_style["color"]:
            colors[y, x: end, :3] = Color.from_hex(token_style["color"])
        if token_style["bgcolor"]:
            colors[y, x: end, 3:] = Color.from_hex(token_style["bgcolor"])
        canvas[y, x: end]["bold"] = token_style["bold"]
        canvas[y, x: end]["italic"] = token_style["italic"]
        canvas[y, x: end]["underline"] = token_style["underline"]
        x = end


PYTHON_LEXER = get_lexer_by_name("Python")
STYLE = get_style_by_name("github-dark")
CODE = """\
class SyntaxApp(App):
    async def on_start(self):
        text_widget = TextWidget()
        text_widget.set_text(CODE)
        self.add_widget(text_widget)
        add_syntax_highlighting(text_widget, PYTHON_LEXER, STYLE)


SyntaxApp().run()
"""

class SyntaxApp(App):
    async def on_start(self):
        text_widget = TextWidget()
        text_widget.set_text(CODE)
        self.add_widget(text_widget)
        add_syntax_highlighting(text_widget, PYTHON_LEXER, STYLE)


SyntaxApp(title="Syntax Highlighting Example").run()
