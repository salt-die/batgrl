import asyncio

from batgrl.gadgets.text import Text, add_text

CORRECT_GUESS = """\
>{}
>Exact match!
>Please wait
>while system
>is accessed.

>"""
INCORRECT_GUESS = """\
>{}
>Entry denied
>{}/9 correct.

>█"""


class Output(Text):
    def __init__(self, header, modal, **kwargs):
        super().__init__(**kwargs)
        self.header = header
        self.modal = modal

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, password):
        self._password = password
        self.tries = 4

    @property
    def tries(self):
        return self._tries

    @tries.setter
    def tries(self, tries):
        self._tries = tries
        self.header.add_str(
            f"{tries} ATTEMPT(S) LEFT:{' █' * tries}".ljust(27),
            pos=(3, 0),
        )

    def attempt(self, password):
        self._slow_add_task.cancel()

        if password == self.password:
            self.canvas[:-5] = self.canvas[5:]
            self.chars[-7:] = " "
            add_text(
                self.canvas[-7:],
                CORRECT_GUESS.format(password),
            )
            self.modal.show(is_win=True)
        else:
            self.canvas[:-3] = self.canvas[3:]
            self.chars[-5:] = " "
            likeness = sum(a == b for a, b in zip(password, self.password))
            add_text(
                self.canvas[-5:],
                INCORRECT_GUESS.format(password, likeness),
            )
            self.tries -= 1
            if self.tries == 0:
                self.modal.show(is_win=False)

    def on_add(self):
        super().on_add()
        self._slow_add_task = asyncio.create_task(asyncio.sleep(0))  # dummy task

    def slow_add_str(self, s):
        self._slow_add_task.cancel()
        self._slow_add_task = asyncio.create_task(self._slow_add_str(s))

    async def _slow_add_str(self, s):
        self.add_str("█".ljust(12), pos=(-1, 1))
        for i, char in enumerate(s):
            await asyncio.sleep(0.04)
            self.add_str(char + "█", pos=(-1, 1 + i))
