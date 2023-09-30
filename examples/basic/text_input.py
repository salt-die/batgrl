from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.text_pad import TextPad
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.textbox import Textbox
from nurses_2.widgets.window import Window

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


class TextPadApp(App):
    async def on_start(self):
        window = Window(pos=(5, 5), size=(15, 30), title="Textpad")
        tp = TextPad()
        window.view = tp
        tp.text = JABBERWOCKY

        # `enter_callback` expects a callable with the textbox as the only argument.
        def enter_callback(textbox):
            textbox.text = ""

        textbox = Textbox(
            pos=(1, 3),
            size=(1, 31),
            enter_callback=enter_callback,
            placeholder="Search...",
            max_chars=50,
        )

        border = TextWidget(
            pos=(1, 0),
            size=(3, 35),
            pos_hint={"x_hint": 0.5, "anchor": "top"},
            default_color_pair=DEFAULT_COLOR_THEME.textbox_primary,
        )
        border.add_border()
        border.add_str("🔍", pos=(1, 1))
        border.add_widget(textbox)

        self.add_widgets(window, border)


if __name__ == "__main__":
    TextPadApp().run()
