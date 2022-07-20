import asyncio
from itertools import product

import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import AYELLOW, ARED
from nurses_2.io import MouseEventType
from nurses_2.widgets.widget import Widget, Easing
from nurses_2.widgets.text_widget import TextWidget

from .graphics import CHECKER_SIZE, x_to_column, Checker, Board

GAME_OVER_MESSAGE = "{} wins! Press `r` to play again."
DRAW_MESSAGE = "It's a draw! Press 'r' to play again."
COLUMN_FULL_MESSAGE = "Column full."
TURN_MESSAGE = "{}'s turn."
PLAYER_NAMES = "Red", "Yellow"


class Connect4(Widget):
    def __init__(self):
        self._board = Board()
        self._label = TextWidget(size=(1, 10), pos_hint=(None, .5), anchor="center")

        h, w = self._board.size

        super().__init__(
            size=(h + 2, w),
            pos_hint=(.5, .5),
            anchor="center",
        )

        self._animation_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._columns = [[]]
        self.reset()

    def display_message(self, message):
        self._label.width = len(message)
        self._label.update_geometry()  # Re-center label
        self._label.add_text(message)

    async def display_message_after(self, message, duration):
        await asyncio.sleep(duration)
        self.display_message(message)

    def reset(self):
        self._animation_task.cancel()

        for column in self._columns:
            for checker in column:
                checker.stop_flash()

        self._columns = [[] for _ in range(7)]
        self._board_array = np.zeros((6, 7), dtype=int)
        self._game_over = False
        self._player = 0

        self.children.clear()
        self.add_widgets(self._label, self._board)

        self.display_message(TURN_MESSAGE.format(self.current_player))

    @property
    def current_player(self) -> str:
        return PLAYER_NAMES[self._player]

    def on_press(self, key_press_event):
        match key_press_event.key:
            case "r" | "R":
                self.reset()

    def check_game(self):
        if checkers := self.is_connect_four():
            self._game_over = True
            self.display_message(GAME_OVER_MESSAGE.format(self.current_player))
            for row, col in checkers:
                self._columns[col][5 - row].flash()
        elif sum(len(col) for col in self._columns) == 42:
            self._game_over = True
            self.display_message(DRAW_MESSAGE)
        else:
            self._player ^= 1
            self.display_message(TURN_MESSAGE.format(self.current_player))

    def is_connect_four(self):
        row, col = self._last_move
        player = self._player + 1
        board = self._board_array

        # Look down
        if row + 3 < 6 and (board[row: row + 4, col] == player).all():
            return tuple((row + i, col) for i in range(4))

        # Look right
        for x in (col - i for i in range(3) if col - i >= 0):
            if x + 3 < 7 and (board[row, x: x + 4] == player).all():
                return tuple((row, x + j) for j in range(4))

        # Look left
        for x in (col + i for i in range(3) if col + i < 7):
            if x - 3 >= 0 and (board[row, x - 3: x + 1] == player).all():
                return tuple((row, x - 3 + j) for j in range(4))

        # Look on the up-left, up-right, down-left, down-right diagonals.
        if checkers := (
            self._diagonal(-1, -1)
            or self._diagonal(-1, 1)
            or self._diagonal(1, -1)
            or self._diagonal(1, 1)
        ):
            return checkers

        return False

    def _diagonal(self, y_step, x_step):
        row, column = self._last_move
        player = self._player + 1
        board = self._board_array

        for y, x in ((row - y_step * i, column - x_step * i) for i in range(3)):
            #Check that both ends of the diagonal are in bounds.
            if not (
                0 <= y < 6
                and 0 <= y + 3 * y_step < 6
                and 0 <= x < 7
                and 0 <= x + 3 * x_step < 7
            ):
                continue

            if all(board[y + y_step * i, x + x_step * i] == player for i in range(4)):
                return tuple((y + y_step * i, x + x_step * i) for i in range(4))

        return False

    def on_click(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and not self._game_over
            and self._animation_task.done()
            and self.collides_point(mouse_event.position)
        ):
            col = x_to_column(self.to_local(mouse_event.position).x)

            if (row := (5 - len(self._columns[col]))) == 0:
                self.display_message(COLUMN_FULL_MESSAGE)
                asyncio.create_task(
                    self.display_message_after(TURN_MESSAGE.format(self.current_player), 2)
                )
                return

            self._last_move = row, col

            h, w = CHECKER_SIZE
            checker = Checker(AYELLOW if self._player else ARED)
            checker.pos = -h, col * w

            self._columns[col].append(checker)
            self._board_array[row, col] = self._player + 1

            self.add_widget(checker)
            self._label.pull_to_front()
            self._board.pull_to_front()

            self._animation_task = asyncio.create_task(
                checker.tween(
                    duration=(row + 1)**2 / 36,
                    easing=Easing.IN_QUAD,
                    on_complete=self.check_game,
                    y=h * row + 2,
                )
            )


run_widget_as_app(Connect4)
