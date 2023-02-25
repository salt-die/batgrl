from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.image import Image
from nurses_2.widgets.text_widget import TextWidget, add_text

from .colors import DEFAULT_COLOR_PAIR
from .effects import BOLDCRT
from .memory import MemoryWidget
from .modal import Modal
from .output import Output

TERMINAL = Path(__file__).parent.parent.parent.parent / "assets" / "fallout_terminal.png"
HEADER = """\
ROBCO INDUSTRIES <TM> TERMLINK PROTOCOL
ENTER PASSWORD NOW

4 ATTEMPT(S) LEFT: █ █ █ █
"""


class HackApp(App):
    async def on_start(self):
        header = TextWidget(size=(5, 39), default_color_pair=DEFAULT_COLOR_PAIR)
        add_text(header.canvas, HEADER)

        modal = Modal(size_hint=(1.0, 1.0), is_enabled=False)

        output = Output(
            header,
            modal,
            size=(17, 13),
            pos=(5, 40),
            default_color_pair=DEFAULT_COLOR_PAIR,
        )

        memory = MemoryWidget(
            output,
            size=(17, 39),
            pos=(5, 0),
            default_color_pair=DEFAULT_COLOR_PAIR,
        )

        modal.memory = memory

        terminal = Image(path=TERMINAL, size=(36, 63), pos_hint=(.5, .5), anchor="center")
        container = BOLDCRT(
            size=(22, 53),
            pos=(5, 5),
            is_transparent=False,
            background_char=" ",
            background_color_pair=DEFAULT_COLOR_PAIR,
        )

        terminal.add_widget(container)
        container.add_widgets(header, memory, output, modal)
        self.add_widget(terminal)

        memory.init_memory()


HackApp(title="Hack", background_color_pair=DEFAULT_COLOR_PAIR).run()
