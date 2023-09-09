"""
Color palette creator.
"""
import cv2
import numpy as np

from nurses_2.app import App
from nurses_2.clamp import clamp
from nurses_2.colors import BLACK, WHITE, Color
from nurses_2.widgets.widget import Widget
from nurses_2.widgets.text_widget import TextWidget
from nurses_2.widgets.behaviors.grabbable import Grabbable

H = 11
"""Height of palette."""

W = 60
"""
Width of palette.

Width must be a multiple of 5 that divides 180.
"""
if W not in {5, 10, 15, 20, 30, 45, 60, 90, 180}:
    raise ValueError("Invalid palette width")

SATURATIONS = 249, 218, 187, 156, 125
"""Saturations of each color in the palette."""

VIBRANCES = 250, 189, 128, 67, 15
"""Vibrances of each color in the palette. """

def hues():
    """
    Hue selector colors.
    """
    hsv = np.full((1, W, 3), 255, np.uint8)
    hsv[0, :, 0] = np.arange(0, 180, 180 // W)
    return cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)

def to_hex(rgb) -> str:
    """
    Convert a RGB color to a hex string.
    """
    return "".join(hex(channel)[2:].zfill(2) for channel in rgb)

def text_color(rgb) -> Color:
    """
    Return text color depending on brightness of rgb.
    """
    if rgb @ (.2126, .7152, .0722) > 255 / 2:
        return BLACK
    return WHITE


class Selector(Grabbable, TextWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.indicator = TextWidget(size=(1, 1), default_color_pair=(255, 255, 255) * 2)
        self.add_widget(self.indicator)
        self.callback = None

    def grab(self, mouse_event):
        super().grab(mouse_event)
        self.grab_update(mouse_event)

    def grab_update(self, mouse_event):
        self.indicator.x = clamp(self.to_local(mouse_event.position).x, 0, self.width - 1)
        if self.callback:
            self.callback()


class PaletteApp(App):
    async def on_start(self):
        hue_selector = Selector(size=(1, W), default_char="▬")
        hue_selector.colors[..., :3] = hues()

        slope_selector = Selector(size=(1, W), pos=(1, 0), default_char="▬")

        palette = TextWidget(size=(H, W), pos=(2, 0))

        def update_palette():
            start_rgb = hue_selector.colors[0, hue_selector.indicator.x, :3]
            start_hue = cv2.cvtColor(start_rgb[None, None], cv2.COLOR_RGB2HSV)[0, 0, 0]
            hue_slopes = np.linspace(-36, 36, W, endpoint=True, dtype=int)

            # Paint slope selector.
            slope_hsv = np.zeros((1, W, 3), np.uint8)
            slope_hsv[0, :, 0] = (start_hue + hue_slopes) % 180
            slope_hsv[0, :, 1] = SATURATIONS[1]
            slope_hsv[0, :, 2] = VIBRANCES[1]
            slope_selector.colors[..., :3] = cv2.cvtColor(slope_hsv, cv2.COLOR_HSV2RGB)

            # Create palette colors.
            slope = hue_slopes[slope_selector.indicator.x]
            palette_hsv = np.zeros((1, 5, 3), np.uint8)
            for i in range(5):
                palette_hsv[0, i] = (start_hue + i * slope) % 180, SATURATIONS[i], VIBRANCES[i]
            palette_rgb = cv2.cvtColor(palette_hsv, cv2.COLOR_HSV2RGB)

            # Paint palette and add hex codes.
            for i in range(5):
                w = W // 5
                x = w * i
                rgb = palette_rgb[0, i]

                palette.colors[:, x: x + w, 3:] = rgb

                offset = (w - 6) // 2
                if offset >= 0:
                    offset += x
                    palette.colors[H // 2, offset: offset + 6, :3] = text_color(rgb)
                    palette.add_str(to_hex(rgb).upper(), pos=(H // 2, offset))

        update_palette()

        hue_selector.callback = slope_selector.callback = update_palette

        container = Widget(size=(H + 2, W), pos_hint=(.5, .5), anchor="center")
        container.add_widgets(hue_selector, slope_selector, palette)
        self.add_widget(container)


PaletteApp(title="Color Palette Creator").run()
