from random import choice, randrange, sample
from pathlib import Path

import numpy as np

from nurses_2.io import MouseEventType, MouseButton
from nurses_2.widgets.text_widget import TextWidget

from .colors import DEFAULT_COLOR_PAIR

NOISE = np.array(list("!\"#$%'()*+,-./:;<>?@[\\]^_`{|}="))

WORD_COUNT = 17
WORD_LENGTH = 9
def create_word_list() -> list[str]:
    path = Path(__file__).parent / "words.txt"
    words = path.read_text().splitlines()
    return [word for word in words if len(word) == WORD_LENGTH]
WORDS = create_word_list()

def memory_to_pos(i):
    y, x = divmod(i, 12)
    if y >= 17:
        y -= 17
        x += 27
    else:
        x += 7
    return y, x

def pos_to_memory(pos):
    y, x = pos

    if y < 0 or y >= 17:
        return

    if x in range(7, 19):
        return y * 12 + x - 7

    if x in range(27, 39):
        return (17 + y) * 12 + x - 27


class MemoryWidget(TextWidget):
    def __init__(self, output, **kwargs):
        super().__init__(**kwargs)
        self.output = output

    def init_memory(self):
        # Memory addresses
        start_address = randrange(0, 0xfe38, 12)
        for i in range(34):
            self.add_str(
                f"0x{start_address + 12 * i:04X}",
                pos=(i % 17, 0 if i < 17 else 20),
            )

        # Create a list of random characters and
        # insert words at random indices.
        total_chars = 12 * 34
        word_chars = WORD_COUNT * WORD_LENGTH
        noise_chars = total_chars - word_chars

        words = sample(WORDS, k=WORD_COUNT)

        word_indices = sample(range(0, noise_chars + 1, 4), k=WORD_COUNT)
        word_indices.sort(reverse=True)
        word_indices = np.array(word_indices)

        memory = list(NOISE[np.random.randint(0, len(NOISE), noise_chars)])
        for i, word in zip(word_indices, words):
            memory[i:] = list(word) + memory[i:]

        word_indices += np.arange(WORD_COUNT)[::-1] * WORD_LENGTH

        self.words = words
        self.word_indices = {i + j: i for i in word_indices for j in range(WORD_LENGTH)}
        self.memory = "".join(memory)

        for i, char in enumerate(self.memory):
            self.canvas["char"][memory_to_pos(i)] = char

        self.output.password = choice(words)
        self.output.canvas["char"] = " "
        self.output.add_str(">█".ljust(13), pos=(-1, 0))

    def on_mouse(self, mouse_event):
        if mouse_event.event_type is MouseEventType.MOUSE_UP:
            return

        self.colors[:] = DEFAULT_COLOR_PAIR

        i = pos_to_memory(self.to_local(mouse_event.position))
        if i is None:
            self.output.slow_add_str("")
            return

        if (start := self.word_indices.get(i)) is not None:
            end = start + WORD_LENGTH
            for j in range(start, end):
                self.colors[memory_to_pos(j)] = DEFAULT_COLOR_PAIR.reversed()

            guess = self.memory[start: end]
            if (
                mouse_event.button is MouseButton.LEFT and
                mouse_event.event_type is MouseEventType.MOUSE_DOWN
            ):
                self.output.attempt(guess)
            else:
                self.output.slow_add_str(guess)
        else:
            self.colors[memory_to_pos(i)] = DEFAULT_COLOR_PAIR.reversed()
            self.output.slow_add_str(self.memory[i])

        return True
