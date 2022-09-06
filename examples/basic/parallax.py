import asyncio
from pathlib import Path

import numpy as np

from nurses_2.app import App
from nurses_2.widgets.parallax import Parallax

ASSETS = Path(__file__).parent.parent / "assets"
PARALLAX = ASSETS / "space_parallax"


class MyApp(App):
    async def on_start(self):
        parallax = Parallax(path=PARALLAX, size_hint=(1.0, 1.0))
        self.add_widget(parallax)

        async def circle_movement():
            angles = np.linspace(0, 2 * np.pi, 400)
            radius = 50

            while True:
                for theta in angles:
                    parallax.offset = radius * np.cos(theta), radius * np.sin(theta)
                    await asyncio.sleep(.016)

        asyncio.create_task(circle_movement())


MyApp(title="Parallax Example").run()
