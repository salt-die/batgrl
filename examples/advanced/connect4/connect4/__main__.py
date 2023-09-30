import asyncio

import numpy as np

from nurses_2.app import run_widget_as_app
from nurses_2.colors import ARED, AYELLOW
from nurses_2.io import MouseEventType
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.widget import Widget

from .graphics import CHECKER_SIZE, Board, Checker, x_to_column

GAME_OVER_MESSAGE = "{} wins! Press `r` to play again."
DRAW_MESSAGE = "It's a draw! Press 'r' to play again."
COLUMN_FULL_MESSAGE = "Column full."
TURN_MESSAGE = "{}'s turn."
PLAYER_NAMES = "Red", "Yellow"


class Connect4(Widget):
    def __init__(self):
        self._board = Board()
        h, w = self._board.size

        super().__init__(size=(h + 2, w), pos_hint={"y_hint": 0.5, "x_hint": 0.5})

        self._label = TextWidget(size=(1, 10), pos_hint={"x_hint": 0.5})
        self.add_widgets(self._board, self._label)

    def on_add(self):
        super().on_add()
        self._animation_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._label_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self.reset()

    def on_remove(self):
        super().on_remove()
        self._animation_task.cancel()
        self._label_task.cancel()

    def display_message(self, message):
        self._label.width = len(message)
        self._label.apply_hints()  # Re-center label
        self._label.add_str(message)

    async def display_message_after(self, message, duration):
        await asyncio.sleep(duration)
        self.display_message(message)

    def reset(self):
        self._animation_task.cancel()

        self._columns = [[] for _ in range(7)]
        self._board_array = np.zeros((6, 7), dtype=int)
        self._game_over = False
        self._player = 0

        for child in self.children.copy():
            if child not in {self._label, self._board}:
                child.destroy()

        self.display_message(TURN_MESSAGE.format(self.current_player))

    @property
    def current_player(self) -> str:
        return PLAYER_NAMES[self._player]

    def on_key(self, key_event):
        match key_event.key:
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
        if row + 3 < 6 and (board[row : row + 4, col] == player).all():
            return tuple((row + i, col) for i in range(4))

        # Look right
        for x in (col - i for i in range(3) if col - i >= 0):
            if x + 3 < 7 and (board[row, x : x + 4] == player).all():
                return tuple((row, x + j) for j in range(4))

        # Look left
        for x in (col + i for i in range(3) if col + i < 7):
            if x - 3 >= 0 and (board[row, x - 3 : x + 1] == player).all():
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
            # Check that both ends of the diagonal are in bounds.
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

    def on_mouse(self, mouse_event):
        if (
            mouse_event.event_type is MouseEventType.MOUSE_DOWN
            and not self._game_over
            and self._animation_task.done()
            and self.collides_point(mouse_event.position)
        ):
            col = x_to_column(self.to_local(mouse_event.position).x)

            if (row := (5 - len(self._columns[col]))) == -1:
                self.display_message(COLUMN_FULL_MESSAGE)
                self._label_task = asyncio.create_task(
                    self.display_message_after(
                        TURN_MESSAGE.format(self.current_player), 2
                    )
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
                checker.fall(h * row + 2, self.check_game)
            )


if __name__ == "__main__":
    run_widget_as_app(Connect4())
