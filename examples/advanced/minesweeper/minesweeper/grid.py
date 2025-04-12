from batgrl.gadgets.text import Text

from .unicode_chars import HEAVY_BOX, LIGHT_BOX


class Grid(Text):
    V_SPACING = 2
    H_SPACING = 4

    def __init__(self, size, is_light: bool, **kwargs):
        h, w = size
        vs, hs = self.V_SPACING, self.H_SPACING

        super().__init__(pos=(1, 0), size=(vs * h + 1, hs * w + 1), **kwargs)

        chars = self.chars

        h, v, tl, tm, tr, bl, bm, br, ml, mm, mr = LIGHT_BOX if is_light else HEAVY_BOX

        chars[::vs] = h
        chars[:, ::hs] = v
        chars[vs:-vs:vs, hs:-hs:hs] = mm

        # Top
        chars[0, hs:-hs:hs] = tm
        # Bottom
        chars[-1, hs:-hs:hs] = bm
        # Left
        chars[vs:-vs:vs, 0] = ml
        # Right
        chars[vs:-vs:vs, -1] = mr

        # Corners
        chars[0, 0] = tl
        chars[0, -1] = tr
        chars[-1, 0] = bl
        chars[-1, -1] = br

    @property
    def cell_center_indices(self):
        vs, hs = self.V_SPACING, self.H_SPACING

        return slice(vs // 2, None, vs), slice(hs // 2, None, hs)
