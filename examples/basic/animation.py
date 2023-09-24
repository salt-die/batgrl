from pathlib import Path

from nurses_2.app import App
from nurses_2.widgets.animation import Animation

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_FRAMES = ASSETS / "caveman"


class AnimationApp(App):
    async def on_start(self):
        animation = Animation(
            size_hint=(0.5, 0.5),
            pos_hint=(0.5, 0.5),
            path=PATH_TO_FRAMES,
            interpolation="nearest",
        )

        self.add_widget(animation)
        animation.play()


if __name__ == "__main__":
    AnimationApp(title="Animation Example").run()
