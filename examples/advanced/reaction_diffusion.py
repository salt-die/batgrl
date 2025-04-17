import asyncio

import cv2
import numpy as np
from batgrl.app import App
from batgrl.colors import Color
from batgrl.gadgets.text import Text

BLOCKS = np.array(list(" .,:;<+*LtCa4U80dQM@▁▂▃▄▅▆▇█▉▊▋▌▍▏░▒▓█▙▚▖"))
KERNEL = np.array([[0.05, 0.2, 0.05], [0.2, -1, 0.2], [0.05, 0.2, 0.05]])
PALETTE = np.array(
    [
        Color.from_hex(hexcode)
        for hexcode in ["0606fa", "4c1bbd", "5a2280", "3f1a43", "0f080e"]
    ]
)


class ReactionDiffusion(Text):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.diffusion_A = 1.0
        self.diffusion_B = 0.5
        self.feed = 0.01624
        self.kill = 0.04465
        self.on_size()

    def on_size(self):
        super().on_size()
        self.clear()
        h, w = self.size
        self.A = np.ones((h, w), dtype=float)
        self.B = np.zeros_like(self.A)
        self.B[: h // 5, : w // 5] = 1

    def on_mouse(self, mouse_event):
        if mouse_event.button == "left" and self.collides_point(mouse_event.pos):
            y, x = self.to_local(mouse_event.pos)
            self.B[y - 1 : y + 3, x - 1 : x + 2] += 0.5
            return True

    def update(self):
        laplace_A = cv2.filter2D(
            self.A, ddepth=-1, kernel=self.diffusion_A * KERNEL, borderType=2
        )
        laplace_B = cv2.filter2D(
            self.B, ddepth=-1, kernel=self.diffusion_B * KERNEL, borderType=2
        )
        react = self.A * self.B**2

        self.A *= 1 - self.feed
        self.A += laplace_A
        self.A -= react
        self.A += self.feed
        np.clip(self.A, 0, 0.9999999, out=self.A)

        self.B *= 1 - self.kill - self.feed
        self.B += laplace_B
        self.B += react
        np.clip(self.B, 0, 0.9999999, out=self.B)

        to_palette = self.A * len(PALETTE)
        to_char = (to_palette % 1) * len(BLOCKS)
        self.canvas["fg_color"] = PALETTE[to_palette.astype(int)]
        self.chars[:] = BLOCKS[to_char.astype(int)]


class ReactionDiffusionApp(App):
    async def on_start(self):
        reaction_diffusion = ReactionDiffusion(
            size_hint={"height_hint": 1.0, "width_hint": 1.0}
        )
        self.add_gadget(reaction_diffusion)
        while True:
            reaction_diffusion.update()
            await asyncio.sleep(0)


if __name__ == "__main__":
    ReactionDiffusionApp(title="Cookin'").run()
