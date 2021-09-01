from nurses_2.widgets import Widget

from .unicode_chars import LIGHT_BOX, HEAVY_BOX


class Grid(Widget):
    V_SPACING = 2
    H_SPACING = 4

    def __init__(self, size, is_light: bool, **kwargs):
        h, w = size
        vs, hs = self.V_SPACING, self.H_SPACING

        super().__init__(pos=(1, 0), size=(vs * h + 1, hs * w + 1), **kwargs)

        canvas = self.canvas

        h, v, tl, tm, tr, bl, bm, br, ml, mm, mr = LIGHT_BOX if is_light else HEAVY_BOX

        canvas[::vs] = h
        canvas[:, ::hs] = v
        canvas[vs: -vs: vs, hs: -hs: hs] = mm

        # Top
        canvas[0, hs: -hs: hs] = tm
        # Bottom
        canvas[-1, hs: -hs: hs] = bm
        # Left
        canvas[vs: -vs: vs, 0] = ml
        # Right
        canvas[vs: -vs: vs, -1] = mr

        # Corners
        canvas[0, 0] = tl
        canvas[0, -1] = tr
        canvas[-1, 0] = bl
        canvas[-1, -1] = br
