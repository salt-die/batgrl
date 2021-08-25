from nurses_2.widgets import Widget

LIGHT_BOX = "─│┌┬┐└┴┘├┼┤"
HEAVY_BOX = "━┃┏┳┓┗┻┛┣╋┫"


class Grid(Widget):
    def __init__(self, size, is_light: bool, **kwargs):
        h, w = size

        super().__init__(size=(2 * h + 1, 4 * w + 1), **kwargs)

        canvas = self.canvas

        h, v, tl, tm, tr, bl, bm, br, ml, mm, mr = LIGHT_BOX if is_light else HEAVY_BOX

        canvas[::2] = h
        canvas[:, ::4] = v
        canvas[2: -2: 2, 4: -4: 4] = mm

        # Top
        canvas[0, 4: -4: 4] = tm
        # Bottom
        canvas[-1, 4: -4: 4] = bm
        # Left
        canvas[2: -2: 2, 0] = ml
        # Right
        canvas[2: -2: 2, -1] = mr

        # Corners
        canvas[0, 0] = tl
        canvas[0, -1] = tr
        canvas[-1, 0] = bl
        canvas[-1, -1] = br
