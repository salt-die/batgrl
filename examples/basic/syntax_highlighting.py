"""Syntax highlighting example."""

from pathlib import Path

from batgrl.app import App
from batgrl.colors import NEPTUNE_PRIMARY_BG, NEPTUNE_PRIMARY_FG, Neptune
from batgrl.gadgets.menu import MenuBar
from batgrl.gadgets.scroll_view import ScrollView
from batgrl.gadgets.text import Text, new_cell
from pygments.styles import get_style_by_name

DARK_STYLES = [
    "dracula",
    "fruity",
    "github-dark",
    "gruvbox-dark",
    "inkpot",
    "lightbulb",
    "material",
    "monokai",
    "native",
    "neptune",
    "nord-darker",
    "nord",
    "one-dark",
    "paraiso-dark",
    "rrt",
    "solarized-dark",
    "stata-dark",
    "vim",
    "zenburn",
]
LIGHT_STYLES = [
    "abap",
    "algol_nu",
    "algol",
    "arduino",
    "autumn",
    "borland",
    "bw",
    "colorful",
    "default",
    "emacs",
    "friendly_grayscale",
    "friendly",
    "gruvbox-light",
    "igor",
    "lilypond",
    "lovelace",
    "manni",
    "murphy",
    "paraiso-light",
    "pastie",
    "perldoc",
    "rainbow_dash",
    "sas",
    "solarized-light",
    "staroffice",
    "stata-light",
    "stata",
    "tango",
    "trac",
    "vs",
    "xcode",
]


def get_style_by_name_(name):
    if name == "neptune":
        return Neptune
    return get_style_by_name(name)


class SyntaxApp(App):
    async def on_start(self):
        code = Path(__file__).read_bytes().decode("utf-8").replace("\r", "")
        text = Text()
        text.set_text(code)
        text.size_hint = {
            "width_hint": 1.0,
            "min_width": text.width,
            "width_offset": -2,
        }
        last_style = "neptune"

        def callback_for(name):
            def callback():
                nonlocal last_style
                last_style = name
                text.add_syntax_highlighting(style=get_style_by_name_(name))

            return callback

        def repaint():
            text.add_syntax_highlighting(style=get_style_by_name_(last_style))

        text.bind("size", repaint)

        dark_menu = {(style, ""): callback_for(style) for style in DARK_STYLES}
        light_menu = {(style, ""): callback_for(style) for style in LIGHT_STYLES}

        sep = Text(
            default_cell=new_cell(
                ord=ord("━"), fg_color=NEPTUNE_PRIMARY_FG, bg_color=NEPTUNE_PRIMARY_BG
            ),
            pos=(1, 0),
            size=(1, 1),
            size_hint={"width_hint": 1.0},
        )
        sv = ScrollView(
            pos=(2, 0),
            size_hint={
                "height_hint": 1.0,
                "width_hint": 1.0,
                "height_offset": -2,
            },
            show_horizontal_bar=False,
        )
        sv.view = text

        self.add_gadgets(sep, sv)
        self.add_gadgets(
            MenuBar.from_iterable(
                [("Dark Styles", dark_menu), ("Light Styles", light_menu)]
            )
        )


if __name__ == "__main__":
    SyntaxApp(title="Syntax Highlighting Example", bg_color=NEPTUNE_PRIMARY_BG).run()
