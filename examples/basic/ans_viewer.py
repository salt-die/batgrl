from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.ans_viewer import AnsViewer

ASSETS = Path(__file__).parent.parent / "assets"
ANS_PATH = ASSETS / "tg-bat.ans"


class AnsApp(App):
    async def on_start(self):
        ans_viewer = AnsViewer(
            path=ANS_PATH, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self.add_gadget(ans_viewer)


if __name__ == "__main__":
    AnsApp(inline=True, inline_height=20).run()
