import asyncio

from nurses_2.app import App
from nurses_2.colors import DEFAULT_COLOR_THEME
from nurses_2.widgets.button import Button
from nurses_2.widgets.progress_bar import ProgressBar
from nurses_2.widgets.text_animation import TextAnimation
from nurses_2.widgets.text_widget import TextWidget

PRIMARY_COLOR = DEFAULT_COLOR_THEME.primary


class MyApp(App):
    async def on_start(self):
        label_a = TextWidget(default_color_pair=PRIMARY_COLOR)
        horizontal_a = ProgressBar(pos=(0, 10), size=(1, 50))

        label_b = TextAnimation(
            frames=["Loading", "Loading.", "Loading..", "Loading..."],
            frame_durations=1 / 12,
            size=(1, 10),
            pos=(2, 0),
            animation_color_pair=PRIMARY_COLOR,
        )
        label_b.play()

        horizontal_b = ProgressBar(pos=(2, 10), size=(1, 50), animation_delay=0.005)

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

        self.add_widgets(
            horizontal_a, horizontal_b, vertical_a, vertical_b, label_a, label_b, button
        )


MyApp(title="Progress Bar Example", background_color_pair=PRIMARY_COLOR).run()
