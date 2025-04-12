import asyncio
from time import perf_counter

import numpy as np
from batgrl.app import App
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.text import Text, add_text

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
║  ║ ⇥   ║   ║   ║   ║   ║   ║   ║   ║   ║   ║   ║ [ ║ ] ║  \\     ║  ║    ║    ║DOWN║  ║
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
╚══════════════════════════════════════════════════════════════════════════════════════╝"""  # noqa
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
 \\               /
  \\             /
   '-..______.-'"""
LEFT_BUTTON = """\
    .────
  .'     │
 /
.
│
 ' .     │
     ' ._'"""
RIGHT_BUTTON = """\
 ────.
│     '.
        \\
         .
         │
│     . '
'_. '"""
SCROLL_WHEEL = """\
.-.
│ │
'-'"""
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
 \\               /
  \\             /
   '-..______.-'"""
SHIFTS = dict(
    zip(
        r'~!@#$%^&*()_+{}|:"<>?ABCDEFGHIJKLMNOPQRSTUVWXYZ',
        r"`1234567890-=[]\;',./abcdefghijklmnopqrstuvwxyz",
    )
)
KEYS = {
    # KEY: (POS, SIZE)
    "escape": ((2, 3), (3, 5)),
    "f1": ((2, 12), (3, 5)),
    "f2": ((2, 16), (3, 5)),
    "f3": ((2, 20), (3, 5)),
    "f4": ((2, 24), (3, 5)),
    "f5": ((2, 31), (3, 5)),
    "f6": ((2, 35), (3, 5)),
    "f7": ((2, 39), (3, 5)),
    "f8": ((2, 43), (3, 5)),
    "f9": ((2, 50), (3, 5)),
    "f10": ((2, 54), (3, 5)),
    "f11": ((2, 58), (3, 5)),
    "f12": ((2, 62), (3, 5)),
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
    "backspace": ((5, 55), (4, 12)),
    "insert": ((5, 69), (4, 6)),
    "home": ((5, 74), (4, 6)),
    "page_up": ((5, 79), (4, 6)),
    "tab": ((8, 3), (4, 7)),
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
    "delete": ((8, 69), (4, 6)),
    "end": ((8, 74), (4, 6)),
    "page_down": ((8, 79), (4, 6)),
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
    "enter": ((11, 54), (4, 13)),
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
    "up": ((14, 74), (4, 6)),
    " ": ((17, 18), (4, 29)),
    "left": ((17, 69), (4, 6)),
    "down": ((17, 74), (4, 6)),
    "right": ((17, 79), (4, 6)),
}


def rainbow(texture):
    """Add a radial rainbow gradient to a texture."""
    h, w, _ = texture.shape
    ys, xs = np.indices((h, w), dtype=float)
    ys -= 0.5 * h
    xs -= 0.5 * w

    colors = 0.5 + 0.5 * np.cos(
        np.arctan2(xs, ys)[..., None] + 3.0 * perf_counter() + (0, 23, 21)
    )
    texture[:] = (colors * 255).astype(int)


class RainbowBehavior:
    def on_add(self):
        super().on_add()
        self._rainbow_task = asyncio.create_task(self._rainbow())

    def on_remove(self):
        self._rainbow_task.cancel()
        super().on_remove()

    async def _rainbow(self):
        while True:
            rainbow(self.canvas["fg_color"])
            await asyncio.sleep(0)


class KeyboardGadget(RainbowBehavior, Text):
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

        self.add_gadgets(
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

    def _show_mods(self, alt, ctrl, shift, in_shift=False):
        shift |= in_shift
        self._lalt.is_visible = alt
        self._ralt.is_visible = alt
        self._lctrl.is_visible = ctrl
        self._rctrl.is_visible = ctrl
        self._lshift.is_visible = shift
        self._rshift.is_visible = shift

    def on_key(self, key_event):
        showkey = self._key_border

        try:
            pos, size = KEYS[SHIFTS.get(key_event.key, key_event.key)]
        except KeyError:
            showkey.is_visible = False
        else:
            showkey.pos = pos
            showkey.size = size
            showkey.chars[:] = " "
            showkey.add_border("heavy", bold=True)
            showkey.is_visible = True
        self._show_mods(
            key_event.alt, key_event.ctrl, key_event.shift, key_event.key in SHIFTS
        )

    def on_mouse(self, mouse_event):
        self._key_border.is_visible = False
        self._show_mods(mouse_event.alt, mouse_event.ctrl, mouse_event.shift)


class MouseGadget(RainbowBehavior, Text):
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

        self.add_gadgets(self._left_button, self._right_button, self._wheel, self._move)

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

        if mouse_event.event_type == "scroll_up":
            self._wheel.is_visible = True
            self._wheel.chars[1, 1] = "↑"
        elif mouse_event.event_type == "scroll_down":
            self._wheel.is_visible = True
            self._wheel.chars[1, 1] = "↓"
        elif mouse_event.button == "middle":
            self._wheel.is_visible = True
            self._wheel.chars[1, 1] = " "
        elif mouse_event.button == "left":
            self._left_button.is_visible = True
        elif mouse_event.button == "right":
            self._right_button.is_visible = True

        if mouse_event.event_type == "mouse_move":
            self._move.is_visible = True


class InputApp(App):
    async def on_start(self):
        keyboard = KeyboardGadget(
            pos_hint={"y_hint": 0.5, "x_hint": 0.0, "anchor": "left"}
        )
        mouse = MouseGadget(pos_hint={"y_hint": 0.5, "x_hint": 1.0, "anchor": "right"})

        container_size = (
            max(keyboard.height, mouse.height),
            keyboard.width + mouse.width + 2,
        )
        container = Gadget(size=container_size, pos_hint={"y_hint": 0.5, "x_hint": 0.5})
        container.add_gadgets(keyboard, mouse)
        self.add_gadget(container)


if __name__ == "__main__":
    InputApp(title="IO Events").run()
