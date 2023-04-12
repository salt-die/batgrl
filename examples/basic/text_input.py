from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.textbox import Textbox
from nurses_2.widgets.text_pad import TextPad
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget
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

        def enter_callback(textbox):
            textbox.text = ""

        # Note that `enter_callback` expects a callable with the textbox as the only argument.
        textbox = Textbox(pos=(1, 1), size=(1, 31), enter_callback=enter_callback, max_chars=50)

        primary = DEFAULT_COLOR_THEME.primary

        border = TextWidget(pos=(1, 0), size=(3, 33), default_color_pair=primary)
        border.add_border()
        border.add_widget(textbox)

        label = TextWidget(pos_hint=(None, .5), anchor="top_center", size=(1, 7), default_color_pair=primary)
        label.add_str("Textbox")

        container = Widget(
            size=(4, 33),
            pos_hint=(None, .5),
            anchor="top_center",
            background_color_pair=primary,
        )
        container.add_widgets(label, border)

        self.add_widgets(window, container)


TextPadApp().run()
