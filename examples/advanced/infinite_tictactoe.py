import asyncio
import colorsys

from batgrl.app import App
from batgrl.colors import BLACK, Color
from batgrl.gadgets.behaviors.button_behavior import ButtonBehavior
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.grid_layout import GridLayout
from batgrl.gadgets.text import Text
from batgrl.text_tools import add_text

BLUES = [Color.from_hex(hexcode) for hexcode in ["2412e8", "170b93", "09053f"]]
REDS = [Color.from_hex(hexcode) for hexcode in ["ea1212", "930b0b", "3d0404"]]
GREY = Color.from_hex("0f0f0f")
LINES = """\
     ┃     ┃
     ┃     ┃
     ┃     ┃
━━━━━╋━━━━━╋━━━━━
     ┃     ┃
     ┃     ┃
     ┃     ┃
━━━━━╋━━━━━╋━━━━━
     ┃     ┃
     ┃     ┃
     ┃     ┃
"""
X = """\
 █ █
 ▄▀▄
 ▀ ▀"""
OH = """\
 █▀█
 █ █
 ▀▀▀"""
WINS = [
    (0, 1, 2),
    (3, 4, 5),
    (6, 7, 8),
    (0, 3, 6),
    (1, 4, 7),
    (2, 5, 8),
    (0, 4, 8),
    (2, 4, 6),
]


class TicTacToeButton(ButtonBehavior, Text):
    def __init__(self, board, **kwargs):
        super().__init__(**kwargs)
        self.board = board

    def update_hover(self):
        if self.player is None:
            self.canvas["bg_color"] = GREY

    def update_normal(self):
        self.canvas["bg_color"] = BLACK

    def on_release(self):
        if self.player is not None or self.board.is_game_over:
            return
        self.board.update(self)


class InfiniteTicTacToe(Gadget):
    def __init__(self):
        super().__init__(size=(11, 17))
        self.lines = Text()
        self.lines.set_text(LINES)
        self.grid = GridLayout(
            grid_rows=3,
            grid_columns=3,
            horizontal_spacing=1,
            vertical_spacing=1,
            size=(11, 17),
            is_transparent=True,
        )
        self.buttons = [TicTacToeButton(board=self, size=(3, 5)) for _ in range(9)]
        self.grid.add_gadgets(self.buttons)
        self.add_gadgets(self.lines, self.grid)
        self.reset()

    def update(self, pressed_button: TicTacToeButton):
        if self.current_player == 0:
            colors = REDS
            symbol = X
        else:
            colors = BLUES
            symbol = OH

        for button in self.buttons:
            if button.player != self.current_player:
                continue
            button.age = (button.age + 1) % 3
            if button.age == 0:
                button.clear()
                button.player = None
            else:
                button.canvas["fg_color"] = colors[button.age]

        pressed_button.player = self.current_player
        pressed_button.canvas["fg_color"] = colors[0]
        add_text(pressed_button.canvas, symbol)

        for a, b, c in WINS:
            if (
                self.current_player
                == self.buttons[a].player
                == self.buttons[b].player
                == self.buttons[c].player
            ):
                self._game_over()
                return

        self.current_player ^= 1

    def _game_over(self):
        self.is_game_over = True
        self._game_over_task = asyncio.create_task(self._game_over_animation())

    async def _game_over_animation(self):
        buttons = [
            button for button in self.buttons if button.player == self.current_player
        ]
        while True:
            for button in buttons:
                r, g, b = (button.canvas["fg_color"][0, 0] / 255).tolist()
                h, s, v = colorsys.rgb_to_hsv(r, g, b)
                h += 0.005
                h %= 1
                r, g, b = colorsys.hsv_to_rgb(h, s, v)
                button.canvas["fg_color"] = int(r * 255), int(g * 255), int(b * 255)
            await asyncio.sleep(0.01)

    def reset(self):
        for button in self.buttons:
            button.clear()
            button.player = None
            button.age = 0
        self.current_player = 0
        self.is_game_over = False

    def dispatch_mouse(self, mouse_event):
        if self.is_game_over:
            if mouse_event.event_type == "mouse_down":
                self._game_over_task.cancel()
                self.reset()
            return True

        return super().dispatch_mouse(mouse_event)


class InfiniteTicTacToeApp(App):
    async def on_start(self):
        tictactoe = InfiniteTicTacToe()
        tictactoe.pos_hint = {"y_hint": 0.5, "x_hint": 0.5}
        self.add_gadget(tictactoe)


if __name__ == "__main__":
    InfiniteTicTacToeApp(title="Infinite Tic-Tac-Toe").run()
