from batgrl.app import App
from batgrl.colors import (
    DEFAULT_COLOR_THEME,
    DEFAULT_PRIMARY_BG,
    DEFAULT_PRIMARY_FG,
    Color,
)
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.text_pad import TextPad
from batgrl.gadgets.textbox import Textbox

SECONDARY_FG = Color.from_hex(DEFAULT_COLOR_THEME["data_table_selected_fg"])
SECONDARY_BG = Color.from_hex(DEFAULT_COLOR_THEME["data_table_selected_bg"])
ACTIVE_COLOR = Color.from_hex(DEFAULT_COLOR_THEME["titlebar_normal_fg"])
INACTIVE_COLOR = Color.from_hex(DEFAULT_COLOR_THEME["titlebar_normal_bg"])

JABBERWOCKY = """
            Jabberwocky
        By Lewis Carroll

’Twas brillig, and the slithy toves
    Did gyre and gimble in the wabe:
All mimsy were the borogoves,
    And the mome raths outgrabe.

“Beware the Jabberwock, my son!
    The jaws that bite, the claws that catch!
Beware the Jubjub bird, and shun
    The frumious Bandersnatch!”

He took his vorpal sword in hand;
    Long time the manxome foe he sought—
So rested he by the Tumtum tree
    And stood awhile in thought.

And, as in uffish thought he stood,
    The Jabberwock, with eyes of flame,
Came whiffling through the tulgey wood,
    And burbled as it came!

One, two! One, two! And through and through
    The vorpal blade went snicker-snack!
He left it dead, and with its head
    He went galumphing back.

“And hast thou slain the Jabberwock?
    Come to my arms, my beamish boy!
O frabjous day! Callooh! Callay!”
    He chortled in his joy.

’Twas brillig, and the slithy toves
    Did gyre and gimble in the wabe:
All mimsy were the borogoves,
    And the mome raths outgrabe.
"""


class BorderOnFocus:
    def on_focus(self):
        super().on_focus()
        self.parent.add_border("near", bold=True, fg_color=ACTIVE_COLOR)

    def on_blur(self):
        super().on_blur()
        self.parent.add_border("near", bold=False, fg_color=INACTIVE_COLOR)


class BorderedOnFocusTextbox(BorderOnFocus, Textbox): ...


class BorderedOnFocusTextPad(BorderOnFocus, TextPad): ...


class TextPadApp(App):
    async def on_start(self):
        textbox = BorderedOnFocusTextbox(
            pos=(1, 4),
            size=(1, 30),
            enter_callback=lambda box: setattr(box, "text", ""),
            placeholder="Search...",
            max_chars=50,
        )
        default_cell = new_cell(fg_color=DEFAULT_PRIMARY_FG, bg_color=SECONDARY_BG)
        textbox_border = Text(pos=(2, 2), size=(3, 35), default_cell=default_cell)
        textbox_border.add_gadget(textbox)
        textbox_border.add_str("🔍 ", bg_color=DEFAULT_PRIMARY_BG, pos=(1, 1))
        textbox_border.canvas["bg_color"][1, 1] = DEFAULT_PRIMARY_BG

        text_pad = BorderedOnFocusTextPad(pos=(1, 1), size=(13, 33))
        text_pad.text = JABBERWOCKY
        text_pad_border = Text(pos=(6, 2), size=(15, 35), default_cell=default_cell)
        text_pad_border.add_gadget(text_pad)

        labels = Text(
            size=(22, 39),
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            default_cell=new_cell(fg_color=SECONDARY_FG, bg_color=SECONDARY_BG),
        )
        labels.add_str("__Textbox__", pos=(1, 16), markdown=True)
        labels.add_str("__Text Pad__", pos=(5, 16), markdown=True)
        labels.add_gadgets(textbox_border, text_pad_border)
        self.add_gadget(labels)


if __name__ == "__main__":
    TextPadApp(title="Text Input Example", bg_color=DEFAULT_PRIMARY_BG).run()
