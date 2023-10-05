import asyncio
from time import monotonic

import numpy as np

from nurses_2.app import App
from nurses_2.io import Key, MouseButton, MouseEventType
from nurses_2.widgets.text import Text, add_text
from nurses_2.widgets.widget import Widget

KEYBOARD = """\
╔══════════════════════════════════════════════════════════════════════════════════════╗
║                                                                                      ║
║  ╔═══╗    ╔═══╦═══╦═══╦═══╗  ╔═══╦═══╦═══╦═══╗  ╔═══╦═══╦═══╦═══╗                    ║
║  ║ESC║    ║F1 ║F2 ║F3 ║F4 ║  ║F5 ║F6 ║F7 ║F8 ║  ║F9 ║F10║F11║F12║                    ║
║  ╚═══╝    ╚═══╩═══╩═══╩═══╝  ╚═══╩═══╩═══╩═══╝  ╚═══╩═══╩═══╩═══╝                    ║
║  ╔═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦═══╦══════════╗  ╔════╦════╦════╗  ║
║  ║ ~ ║ ! ║ @ ║ # ║ $ ║ % ║ ^ ║ & ║ * ║ ( ║ ) ║ _ ║ + ║ BACKSPACE║  ║INS ║HOME║PAGE║  ║
║  ║ ` ║ 1 ║ 2 ║ 3 ║ 4 ║ 5 ║ 6 ║ 7 ║ 8 ║ 9 ║ 0 ║ - ║ = ║   ←      ║  ║    ║    ║ UP ║  ║
║  ╠═══╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦═╩═╦════════╣  ╠════╬════╬════╣  ║
║  ║TAB  ║ Q ║ W ║ E ║ R ║ T ║ Y ║ U ║ I ║ O ║ P ║ { ║ } ║  |     ║  ║DEL ║END ║PAGE║  ║
║  ║ ⇥   ║   ║   ║   ║   ║   ║   ║   ║   ║   ║   ║ [ ║ ] ║  \     ║  ║    ║    ║DOWN║  ║
║  ╠═════╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩════════╣  ╚════╩════╩════╝  ║
║  ║CAPS  ║ A ║ S ║ D ║ F ║ G ║ H ║ J ║ K ║ L ║ : ║ " ║      ENTER║                    ║
║  ║LOCK  ║   ║   ║   ║   ║   ║   ║   ║   ║   ║ ; ║ ' ║         ⏎ ║                    ║
║  ╠══════╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩╦══╩═══════════╣       ╔════╗       ║
║  ║SHIFT  ║ Z ║ X ║ C ║ V ║ B ║ N ║ M ║ < ║ > ║ ? ║         SHIFT║       ║  ↑ ║       ║
║  ║ ↑     ║   ║   ║   ║   ║   ║   ║   ║ , ║ . ║ / ║            ↑ ║       ║    ║       ║
║  ╠════╦══╩═╦═╩══╦╩═══╩═══╩═══╩═══╩═══╩═══╩══╦╩═══╬════╦═════════╣  ╔════╬════╬════╗  ║
║  ║CTRL║ ▓░ ║ALT ║                           ║ALT ║ ▓░ ║     CTRL║  ║  ← ║  ↓ ║  → ║  ║
║  ║    ║ ░▓ ║    ║                           ║    ║ ░▓ ║         ║  ║    ║    ║    ║  ║
║  ╚════╩════╩════╩═══════════════════════════╩════╩════╩═════════╝  ╚════╩════╩════╝  ║
║                                                                                      ║
╚══════════════════════════════════════════════════════════════════════════════════════╝
"""
MOUSE = """\
    .─────────.
  .'     │     '.
 /      .-.      \\
.       │ │       .
│       '-'       │
│' .     │     . '│
│    ' ._'_. '    │
│                 │
│                 │
│                 │
│                 │
'                 '
 \               /
  \             /
   '-..______.-'
"""
LEFT_BUTTON = """\
    .────
  .'     │
 /
.
│
 ' .     │
     ' ._'
"""
RIGHT_BUTTON = """\
 ────.
│     '.
        \\
         .
         │
│     . '
'_. '
"""
SCROLL_WHEEL = """\
.-.
│ │
'-'
"""
MOUSE_MOVE = """\
    .─────────.
  .'           '.
 /               \\
.                 .
│                 │
│                 │
│                 │
│                 │
│                 │
│                 │
│                 │
'                 '
 \               /
  \             /
   '-..______.-'
"""
SHIFTS = dict(
    zip(
        r'~!@#$%^&*()_+{}|:"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        r"`1234567890-=[]\;',./abcdefghijklmnopqrstuvwxyz",
    )
)
KEYS = {
    # KEY             POS      SIZE
    Key.Escape: ((2, 3), (3, 5)),
    Key.F1: ((2, 12), (3, 5)),
    Key.F2: ((2, 16), (3, 5)),
    Key.F3: ((2, 20), (3, 5)),
    Key.F4: ((2, 24), (3, 5)),
    Key.F5: ((2, 31), (3, 5)),
    Key.F6: ((2, 35), (3, 5)),
    Key.F7: ((2, 39), (3, 5)),
    Key.F8: ((2, 43), (3, 5)),
    Key.F9: ((2, 50), (3, 5)),
    Key.F10: ((2, 54), (3, 5)),
    Key.F11: ((2, 58), (3, 5)),
    Key.F12: ((2, 62), (3, 5)),
    "`": ((5, 3), (4, 5)),
    "1": ((5, 7), (4, 5)),
    "2": ((5, 11), (4, 5)),
    "3": ((5, 15), (4, 5)),
    "4": ((5, 19), (4, 5)),
    "5": ((5, 23), (4, 5)),
    "6": ((5, 27), (4, 5)),
    "7": ((5, 31), (4, 5)),
    "8": ((5, 35), (4, 5)),
    "9": ((5, 39), (4, 5)),
    "0": ((5, 43), (4, 5)),
    "-": ((5, 47), (4, 5)),
    "=": ((5, 51), (4, 5)),
    Key.Backspace: ((5, 55), (4, 12)),
    Key.Insert: ((5, 69), (4, 6)),
    Key.Home: ((5, 74), (4, 6)),
    Key.PageUp: ((5, 79), (4, 6)),
    Key.Tab: ((8, 3), (4, 7)),
    "q": ((8, 9), (4, 5)),
    "w": ((8, 13), (4, 5)),
    "e": ((8, 17), (4, 5)),
    "r": ((8, 21), (4, 5)),
    "t": ((8, 25), (4, 5)),
    "y": ((8, 29), (4, 5)),
    "u": ((8, 33), (4, 5)),
    "i": ((8, 37), (4, 5)),
    "o": ((8, 41), (4, 5)),
    "p": ((8, 45), (4, 5)),
    "[": ((8, 49), (4, 5)),
    "]": ((8, 53), (4, 5)),
    "\\": ((8, 57), (4, 10)),
    Key.Delete: ((8, 69), (4, 6)),
    Key.End: ((8, 74), (4, 6)),
    Key.PageDown: ((8, 79), (4, 6)),
    "a": ((11, 10), (4, 5)),
    "s": ((11, 14), (4, 5)),
    "d": ((11, 18), (4, 5)),
    "f": ((11, 22), (4, 5)),
    "g": ((11, 26), (4, 5)),
    "h": ((11, 30), (4, 5)),
    "j": ((11, 34), (4, 5)),
    "k": ((11, 38), (4, 5)),
    "l": ((11, 42), (4, 5)),
    ";": ((11, 46), (4, 5)),
    "'": ((11, 50), (4, 5)),
    Key.Enter: ((11, 54), (4, 13)),
    "z": ((14, 11), (4, 5)),
    "x": ((14, 15), (4, 5)),
    "c": ((14, 19), (4, 5)),
    "v": ((14, 23), (4, 5)),
    "b": ((14, 27), (4, 5)),
    "n": ((14, 31), (4, 5)),
    "m": ((14, 35), (4, 5)),
    ",": ((14, 39), (4, 5)),
    ".": ((14, 43), (4, 5)),
    "/": ((14, 47), (4, 5)),
    Key.Up: ((14, 74), (4, 6)),
    " ": ((17, 18), (4, 29)),
    Key.Left: ((17, 69), (4, 6)),
    Key.Down: ((17, 74), (4, 6)),
    Key.Right: ((17, 79), (4, 6)),
}


def rainbow(texture):
    """
    Add a radial rainbow gradient to a texture.
    """
    h, w, _ = texture.shape
    ys, xs = np.indices((h, w), dtype=float)
    ys -= 0.5 * h
    xs -= 0.5 * w

    colors = 0.5 + 0.5 * np.cos(
        np.arctan2(xs, ys)[..., None] + 3.0 * monotonic() + (0, 23, 21)
    )
    texture[..., :3] = (colors * 255).astype(int)


class RainbowBehavior:
    def on_add(self):
        super().on_add()
        self._rainbow_task = asyncio.create_task(self._rainbow())

    def on_remove(self):
        self._rainbow_task.cancel()
        super().on_remove()

    async def _rainbow(self):
        while True:
            rainbow(self.colors)
            await asyncio.sleep(0)


class KeyboardWidget(RainbowBehavior, Text):
    def __init__(self, **kwargs):
        super().__init__(size=(23, 88), **kwargs)
        add_text(self.canvas, KEYBOARD)
        common = dict(is_visible=False, is_transparent=True)
        self._key_border = Text(**common)
        self._lshift = Text(pos=(14, 3), size=(4, 9), **common)
        self._rshift = Text(pos=(14, 51), size=(4, 16), **common)
        self._lctrl = Text(pos=(17, 3), size=(4, 6), **common)
        self._rctrl = Text(pos=(17, 56), size=(4, 11), **common)
        self._lalt = Text(pos=(17, 13), size=(4, 6), **common)
        self._ralt = Text(pos=(17, 46), size=(4, 6), **common)

        self.add_widgets(
            self._lshift,
            self._rshift,
            self._lctrl,
            self._rctrl,
            self._lalt,
            self._ralt,
            self._key_border,
        )
        for child in self.children:
            child.add_border("heavy", bold=True)

    def _show_mods(self, mods, in_shift=False):
        alt, ctrl, shift = mods
        shift |= in_shift
        self._lalt.is_visible = alt
        self._ralt.is_visible = alt
        self._lctrl.is_visible = ctrl
        self._rctrl.is_visible = ctrl
        self._lshift.is_visible = shift
        self._rshift.is_visible = shift

    def on_key(self, key_event):
        key, mods = key_event
        showkey = self._key_border

        try:
            pos, size = KEYS[SHIFTS.get(key, key)]
        except KeyError:
            showkey.is_visible = False
        else:
            showkey.pos = pos
            showkey.size = size
            showkey.canvas["char"][:] = " "
            showkey.add_border("heavy", bold=True)
            showkey.is_visible = True
        self._show_mods(mods, key in SHIFTS)

    def on_mouse(self, mouse_event):
        self._key_border.is_visible = False
        self._show_mods(mouse_event.mods)


class MouseWidget(RainbowBehavior, Text):
    def __init__(self, **kwargs):
        super().__init__(size=(15, 19), **kwargs)
        common = dict(is_visible=False, is_transparent=True)
        self._left_button = Text(size=(7, 10), **common)
        self._right_button = Text(size=(7, 10), pos=(0, 9), **common)
        self._wheel = Text(size=(3, 3), pos=(2, 8), **common)
        self._move = Text(size=(15, 19), **common)

        add_text(self.canvas, MOUSE)
        add_text(self._left_button.canvas, LEFT_BUTTON)
        add_text(self._right_button.canvas, RIGHT_BUTTON)
        add_text(self._wheel.canvas, SCROLL_WHEEL)
        add_text(self._move.canvas, MOUSE_MOVE)

        self.add_widgets(self._left_button, self._right_button, self._wheel, self._move)

    def on_key(self, key_event):
        self._left_button.is_visible = False
        self._right_button.is_visible = False
        self._wheel.is_visible = False
        self._move.is_visible = False

    def on_mouse(self, mouse_event):
        self._left_button.is_visible = False
        self._right_button.is_visible = False
        self._wheel.is_visible = False
        self._move.is_visible = False

        _, event_type, button, _, _ = mouse_event

        if event_type is MouseEventType.SCROLL_UP:
            self._wheel.is_visible = True
            self._wheel.canvas["char"][1, 1] = "↑"
        elif event_type is MouseEventType.SCROLL_DOWN:
            self._wheel.is_visible = True
            self._wheel.canvas["char"][1, 1] = "↓"
        elif button is MouseButton.MIDDLE:
            self._wheel.is_visible = True
            self._wheel.canvas["char"][1, 1] = " "
        elif button is MouseButton.LEFT:
            self._left_button.is_visible = True
        elif button is MouseButton.RIGHT:
            self._right_button.is_visible = True

        if event_type is MouseEventType.MOUSE_MOVE:
            self._move.is_visible = True


class InputApp(App):
    async def on_start(self):
        keyboard = KeyboardWidget(
            pos_hint={"y_hint": 0.5, "x_hint": 0.0, "anchor": "left"}
        )
        mouse = MouseWidget(pos_hint={"y_hint": 0.5, "x_hint": 1.0, "anchor": "right"})

        container_size = (
            max(keyboard.height, mouse.height),
            keyboard.width + mouse.width + 2,
        )
        container = Widget(size=container_size, pos_hint={"y_hint": 0.5, "x_hint": 0.5})
        container.add_widgets(keyboard, mouse)
        self.add_widget(container)


if __name__ == "__main__":
    InputApp(title="IO Events").run()
