"""An example showcasing movement along a path made up of Bezier curves."""

import asyncio
from itertools import cycle
from pathlib import Path

import numpy as np
from batgrl.app import App
from batgrl.colors import (
    ABLUE,
    AGREEN,
    ARED,
    AYELLOW,
    DEFAULT_PRIMARY_BG,
    DEFAULT_PRIMARY_FG,
    gradient,
)
from batgrl.gadgets.graphics import Graphics
from batgrl.gadgets.image import Image
from batgrl.gadgets.text import Text, new_cell
from batgrl.geometry import BezierCurve, Easing, move_along_path

LOGO = Path(__file__).parent / ".." / "assets" / "python_discord_logo.png"
BG_SIZE = (30, 80)
GRADIENTS = [
    gradient(ARED, AGREEN, 100),
    gradient(AGREEN, ABLUE, 100),
    gradient(ABLUE, AYELLOW, 100),
]


class PathApp(App):
    async def on_start(self):
        bg = Graphics(size=BG_SIZE, default_color=(*DEFAULT_PRIMARY_BG, 255))
        image = Image(path=LOGO, size=(15, 30), alpha=0.85)
        label = Text(
            default_cell=new_cell(
                fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            ),
            is_transparent=True,
        )

        self.add_gadgets(bg, image, label)

        for easing in cycle(Easing.__args__):
            label.set_text(f"Easing: {easing}")
            control_points = np.random.random((7, 2)) * BG_SIZE
            path = [
                BezierCurve(control_points[:3]),
                BezierCurve(control_points[2:5]),
                BezierCurve(control_points[4:]),
            ]

            # Draw curve:
            bg.clear()
            for curve, gradient_ in zip(path, GRADIENTS):
                points = curve.evaluate(np.linspace(0, 1, 100)).astype(int)
                points[:, 0] *= 2
                for (y, x), color in zip(points, gradient_):
                    bg.texture[y : y + 2, x] = color

            await move_along_path(image, path=path, speed=20, easing=easing)
            await asyncio.sleep(1)


if __name__ == "__main__":
    PathApp(title="Motion Example", bg_color=DEFAULT_PRIMARY_BG).run()
