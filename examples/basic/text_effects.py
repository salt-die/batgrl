"""
An example of text effects.

Text effects are recreations of the effects from https://github.com/ChrisBuilds/terminaltexteffects.
To use a text effect simply pass in a `Text` gadget and await the effect.
"""

import asyncio
from pathlib import Path

import numpy as np
from batgrl.app import App
from batgrl.colors import DEFAULT_PRIMARY_BG, DEFAULT_PRIMARY_FG
from batgrl.figfont import FIGFont
from batgrl.gadgets.text import Text, new_cell
from batgrl.gadgets.text_effects import (
    beams_effect,
    black_hole_effect,
    ring_effect,
    spotlights_effect,
)


def make_logo():
    assets = Path(__file__).parent.parent / "assets"
    font = FIGFont.from_path(assets / "delta_corps_priest_1.flf")
    logo = font.render_array("batgrl")
    return np.append(
        logo, [list("badass terminal graphics library".center(logo.shape[1]))], axis=0
    )


LOGO = make_logo()


class TextEffectsApp(App):
    async def on_start(self):
        text = Text(
            size=(30, 80),
            default_cell=new_cell(
                fg_color=DEFAULT_PRIMARY_FG, bg_color=DEFAULT_PRIMARY_BG
            ),
        )
        text.canvas[10:20, 3:77]["char"] = LOGO

        self.add_gadget(text)

        # Note: Do not modify text's size during effects.
        await beams_effect(text)
        await asyncio.sleep(2)
        await black_hole_effect(text)
        await asyncio.sleep(2)
        await ring_effect(text)
        await asyncio.sleep(2)
        await spotlights_effect(text)


if __name__ == "__main__":
    TextEffectsApp(title="Text Effects", bg_color=DEFAULT_PRIMARY_BG).run()
