import numpy as np
from prompt_toolkit.styles import DEFAULT_ATTRS


class Screen:
    """Contents of the screen.  Stores and renders all panels.
    """
    __slots__ = 'env_out', 'panels', 'content', 'attrs',

    def __init__(self, env_out, panels=None):
        self.env_out = env_out
        self.panels = panels or [ ]

        self.reset(env_out.get_size())

    def reset(self, dim):
        self.content = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, None, dtype=object)
        self.attrs[:] = ((DEFAULT_ATTRS, ), )

    @property
    def dim(self):
        return self.content.shape

    @property
    def height(self):
        return self.content.shape[0]

    @property
    def width(self):
        return self.content.shape[1]

    @property
    def middle(self):
        return self.height // 2, self.width // 2

    def render(self):
        """Paint screen to output.
        """
        content = self.content
        attrs = self.attrs
        content[:] = " "
        attrs[:] = ((DEFAULT_ATTRS, ), )

        h, w = content.shape

        panels = self.panels
        panels.sort()  # Sorted according to z-index.

        # Very short names will be used as this is a performance-critical loop.
        # st, dt, sb, db, sl, dl, sr, dr stand for source_top, destination_top, source_bottom,
        # destination_bottom, source_left, destination_left, source_right, destination_right.
        for p in panels:
            # not visible or offscreen
            if (
                not p.is_visible
                or p.top >= h
                or p.bottom < 0
                or p.left >= w
                or p.right < 0
            ):
                continue

            pt = p.top
            pb = p.bottom
            pl = p.left
            pr = p.right

            if pt < 0:
                st = -pt
                dt = 0

                if pb >= h:        # panel-top is off-screen and panel-bottom is off-screen
                    sb = h + st
                    db = h
                else:              # panel-top is off-screen and panel-bottom is on-screen
                    sb = p.height
                    db = pb
            else:
                st =  0
                dt = pt

                if pb >= h:        # panel-top is on-screen and panel-bottom is off-screen
                    sb = h - dt
                    db = h
                else:              # panel-top is on-screen and panel-bottom is on-screen
                    sb = p.height
                    db = pb

            if pl < 0:
                sl = -pl
                dl = 0

                if pr >= w:        # panel-left is off-screen and panel-right is off-screen
                    sr = w + sl
                    dr = w
                else:              # panel-left is off-screen and panel-right is on-screen
                    sr = p.width
                    dr = pr
            else:
                sl = 0
                dl = pl

                if pr >= w:        # panel-left is on-screen and panel-right is off-screen
                    sr = w - dl
                    dr = w
                else:              # panel-left is on-screen and panel-right is on-screen
                    sr = p.width
                    dr = pr

            content[dt: db, dl: dr] = p.content[st: sb, sl: sr]
            attrs[dt: db, dl: dr] = p.attrs[st: sb, sl: sr]

        env_out = self.env_out

        # Avoiding attribute lookups.
        goto = env_out.cursor_goto
        set_attr = env_out.set_attributes
        write = env_out.write

        depth = env_out.get_default_color_depth()

        for i, (line, attr_row) in enumerate(zip(content, attrs)):
            goto(i, 0)

            for char, attr in zip(line, attr_row):
                set_attr(attr, depth)
                write(char)

        env_out.flush()
