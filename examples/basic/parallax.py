import asyncio
from itertools import cycle
from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.parallax import Parallax
from batgrl.geometry import points_on_circle

ASSETS = Path(__file__).parent.parent / "assets"
PARALLAX = ASSETS / "space_parallax"


class ParallaxApp(App):
    async def on_start(self):
        parallax = Parallax(
            path=PARALLAX, size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self.add_gadget(parallax)

        for parallax.offset in cycle(points_on_circle(100, radius=50)):
            await asyncio.sleep(0)


if __name__ == "__main__":
    ParallaxApp(title="Parallax Example").run()
