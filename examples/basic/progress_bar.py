import asyncio

from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.gadgets.button import Button
from batgrl.gadgets.progress_bar import ProgressBar
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.text_animation import TextAnimation


class ProgressBarApp(App):
    async def on_start(self):
        label_a = Text(
            default_cell=new_cell(
                fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            )
        )
        horizontal_a = ProgressBar(pos=(0, 10), size=(1, 50))

        label_b = TextAnimation(
            frames=["Loading", "Loading.", "Loading..", "Loading..."],
            frame_durations=1 / 12,
            size=(1, 10),
            pos=(2, 0),
            animation_fg_color=DEFAULT_PRIMARY_FG,
            animation_bg_color=DEFAULT_PRIMARY_BG,
        )
        label_b.play()

        horizontal_b = ProgressBar(pos=(2, 10), size=(1, 50), animation_delay=0)

        vertical_a = ProgressBar(size=(5, 1), is_horizontal=False)
        vertical_a.top = horizontal_b.bottom + 1

        vertical_b = ProgressBar(size=(5, 1), is_horizontal=False)
        vertical_b.pos = vertical_a.top, vertical_a.right + 1

        async def update_progress():
            for i in range(500):
                progress = (i + 1) / 500
                horizontal_a.progress = progress
                vertical_a.progress = progress
                label_a.set_text(f"{int(progress * 100)}%".rjust(9))
                await asyncio.sleep(1 / 40)

        update_task = asyncio.create_task(update_progress())

        def reset_progress():
            nonlocal update_task
            update_task.cancel()
            update_task = asyncio.create_task(update_progress())

        button = Button(
            pos=(4, 5), size=(5, 55), label="Reset", callback=reset_progress
        )

        self.add_gadgets(
            horizontal_a, horizontal_b, vertical_a, vertical_b, label_a, label_b, button
        )


if __name__ == "__main__":
    ProgressBarApp(title="Progress Bar Example", bg_color=DEFAULT_PRIMARY_BG).run()
