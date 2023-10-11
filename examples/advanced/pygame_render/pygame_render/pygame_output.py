"""
Output for pygame.
"""
from pathlib import Path

import numpy as np
import pygame as pg
import pygame.freetype as ft
from wcwidth import wcwidth

from batgrl.gadgets._root import _Root
from batgrl.geometry import Size

from . import FONT_FULL_WIDTH, FONT_HEIGHT, FONT_WIDTH


class PygameOutput:
    def get_size(self) -> Size:
        w, h = pg.display.get_window_size()
        return Size(h // FONT_HEIGHT, w // FONT_WIDTH)

    def set_title(self, title: str):
        pg.display.set_caption(title)

    def __enter__(self):
        pg.init()
        self.window = pg.display.set_mode(
            (120 * FONT_WIDTH, 40 * FONT_HEIGHT), pg.RESIZABLE
        )
        pg.scrap.init()

        fonts = Path(__file__).parent.parent.parent.parent / "assets" / "fonts"
        self.regular_font = ft.Font(
            fonts / "NotoSansMono-Regular.ttf", (FONT_FULL_WIDTH, FONT_HEIGHT + 1)
        )
        self.emoji_font = ft.Font(
            fonts / "NotoEmoji-Regular.ttf", (FONT_FULL_WIDTH, FONT_HEIGHT + 1)
        )
        # The true font height will be 1 pixel larger than FONT_HEIGHT only to be
        # clipped later in `render_frame`. This should mostly eliminate extra vertical
        # spacing, but introduces a very slight horizontal clipping of some characters.
        # To fix the horizontal clipping the width is reduced by 1, but this introduces
        # some extra horizontal spacing...*sigh*. There's probably a better way, but
        # this'll do for now.
        self.regular_font.size = (
            FONT_FULL_WIDTH - 1,
            (FONT_HEIGHT + 1)
            * (FONT_HEIGHT + 1)
            / self.regular_font.get_sized_height(),
        )
        self.regular_font.pad = True
        self.emoji_font.size = (
            FONT_FULL_WIDTH - 1,
            (FONT_HEIGHT + 1) * (FONT_HEIGHT + 1) / self.emoji_font.get_sized_height(),
        )
        self.emoji_font.pad = True

    def __exit__(self, exc_type, exc_value, traceback):
        pg.quit()
        del self.window, self.regular_font, self.emoji_font

    def render_frame(self, root: _Root):
        canvas = root.canvas
        colors = root.colors
        h, w = root.size
        ys, xs = np.indices((h, w)).reshape(2, h * w)
        for y, x, style, color_pair in zip(ys, xs, canvas[ys, xs], colors[ys, xs]):
            char, bold, italic, underline, strikethrough, overline = style

            if char == "":
                if x == 0 or wcwidth(canvas["char"][y, x - 1]) != 2:
                    char = " "
                else:
                    continue
            elif x + 1 < w and canvas["char"][y, x + 1] != "" and wcwidth(char) == 2:
                char = " "

            if ord(char) >= 0x1F000:  # Heuristic for emoji
                font = self.emoji_font
            else:
                font = self.regular_font

            fr, fg, fb, br, bg, bb = color_pair
            font.fgcolor = fr, fg, fb, 255
            font.bgcolor = br, bg, bb, 255
            font.strong = bool(bold)
            font.oblique = bool(italic)
            font.underline = bool(underline or overline or strikethrough)
            # Pygame freetype fonts only render one of underline, overline or
            # strikethrough, so an arbitrary preference order is used below:
            if strikethrough:
                font.underline_adjstment = -0.3
            elif underline:
                font.underline_adjustment = 1.0
            elif overline:
                font.underline_adjstment = -0.8
            srf, rect = font.render(str(char))
            if rect.x < 0:
                pg.PixelArray(srf)[: -rect.x, :] = (br, bg, bb, 0)
            self.window.blit(
                srf,
                (x * FONT_WIDTH + rect.x, y * FONT_HEIGHT),
                (0, 1, FONT_FULL_WIDTH, FONT_HEIGHT),
            )
        pg.display.update()
