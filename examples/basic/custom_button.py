"""A custom animated button example. Terminal font should support octants."""

import asyncio
from pathlib import Path

from batgrl.app import App
from batgrl.gadgets.behaviors.toggle_button_behavior import ToggleButtonBehavior
from batgrl.gadgets.gadget import Gadget
from batgrl.gadgets.image import Image
from batgrl.texture_tools import read_texture

ASSETS = Path(__file__).parent.parent / "assets" / "custom_button"
BUTTON_ON = read_texture(ASSETS / "on.png")
BUTTON_OFF = read_texture(ASSETS / "off.png")
BUTTON_ON_MID = read_texture(ASSETS / "on-mid.png")
BUTTON_OFF_MID = read_texture(ASSETS / "off-mid.png")


class CustomToggleButton(ToggleButtonBehavior, Gadget):
    def __init__(self, *args, **kwargs):
        self._animate_task = None
        super().__init__(*args, **kwargs)
        self.image = Image(
            size=(2, 8),
            blitter="octant",
            pos_hint={"x_hint": 0.5, "y_hint": 0.5},
            is_transparent=False,
        )
        self.add_gadget(self.image)

    def update_on(self):
        if self._animate_task is not None:
            self._animate_task.cancel()
        self._animate_task = asyncio.create_task(
            self._animate_toggle(BUTTON_ON_MID, BUTTON_ON)
        )

    def update_off(self):
        if self._animate_task is not None:
            self._animate_task.cancel()
        self._animate_task = asyncio.create_task(
            self._animate_toggle(BUTTON_OFF_MID, BUTTON_OFF)
        )

    async def _animate_toggle(self, image_1, image_2):
        self.image.texture = image_1
        await asyncio.sleep(0.1)
        self.image.texture = image_2


class CustomButtonApp(App):
    async def on_start(self):
        toggle_button = CustomToggleButton(size=(2, 8))
        self.add_gadget(toggle_button)


if __name__ == "__main__":
    CustomButtonApp().run()
