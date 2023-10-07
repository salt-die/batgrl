from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.animation import Animation

ASSETS = Path(__file__).parent.parent / "assets"
PATH_TO_FRAMES = ASSETS / "caveman"


class AnimationApp(App):
    async def on_start(self):
        animation = Animation(
            size_hint={"height_hint": 0.5, "width_hint": 0.5},
            pos_hint={"y_hint": 0.5, "x_hint": 0.5},
            path=PATH_TO_FRAMES,
            interpolation="nearest",
        )

        self.add_gadget(animation)
        animation.play()


if __name__ == "__main__":
    AnimationApp(title="Animation Example").run()
