import numpy as np
from prompt_toolkit.styles import DEFAULT_ATTRS
from prompt_toolkit.output.color_depth import ColorDepth

NO_ATTRS = ((DEFAULT_ATTRS, ), )


class Widget:
    """A generic TUI element.
    """
    def __init__(self, dim, pos=(0, 0), *, is_transparent=False, is_visible=True, parent=None):
        self.top, self.left = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible

        self.parent = parent
        self.children = [ ]

        self.content = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, None, dtype=object)
        self.attrs[:] = NO_ATTRS

    def resize(self, dim):
        old_content = self.content
        old_attrs = self.attrs

        old_h, old_w = old_content.shape
        h, w = dim

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.content = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, None, dtype=object)
        self.attrs[:] = NO_ATTRS

        self.content[:copy_h, :copy_w] = old_content[:copy_h, :copy_w]
        self.attrs[:copy_h, :copy_w] = old_attrs[:copy_h, :copy_w]

        for child in self.children:
            child.update_geometry(dim)

    def update_geometry(self, parent_dim):
        """Called when first added to parent or parent has resized.
        """

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
    def bottom(self):
        return self.top + self.height

    @property
    def right(self):
        return self.left + self.width

    @property
    def middle(self):
        return self.height // 2, self.width // 2

    @property
    def root(self):
        """The root widget.
        """
        return self.parent.root

    def add_widget(self, widget):
        """Add widget.
        """
        self.children.append(widget)
        widget.parent = self
        widget.update_geometry(self.dim)

    def remove_widget(self, widget):
        """Remove widget.
        """
        self.children.remove(widget)
        widget.parent = None

    def pull_to_front(self, widget):
        """Move widget to end of widget stack so that it is drawn last.
        """
        self.children.remove(widget)
        self.children.append(widget)

    def walk_from_root(self):
        """Yield all descendents of the root widget.
        """
        yield from self.root.walk()

    def walk(self):
        """Yield self and all descendents.
        """
        yield self
        for child in widget.children:
            yield from child.walk()

    def erase(self):
        """Clear the current contents.
        """
        self.content[:] = " "
        self.attrs[:] = NO_ATTRS

    def _render_child(self, child):
        """Render child and paint child's contents into our own.
        """
        content = self.content
        h, w = content.shape

        ct = child.top
        cb = child.bottom
        cl = child.left
        cr = child.right

        # Child is not visible or off-screen.
        if (
            not child.is_visible
            or ct >= h
            or cb < 0
            or cl >= w
            or cr < 0
        ):
            return

        child.render()

        ##################################################################
        # Four cases for top / bottom of child:                          #
        #     1) child top is off-screen and child bottom is off-screen. #
        #               +-------+                                        #
        #            +--| child |------------+                           #
        #            |  |       |   parent   |                           #
        #            +--|       |------------+                           #
        #               +-------+                                        #
        #     2) child top is off-screen and child bottom is on-screen.  #
        #               +-------+                                        #
        #            +--| child |------------+                           #
        #            |  +-------+   parent   |                           #
        #            +-----------------------+                           #
        #                                                                #
        #     3) child top is on-screen and child bottom is off-screen.  #
        #            +-----------------------+                           #
        #            |  +-------+   parent   |                           #
        #            +--| child |------------+                           #
        #               +-------+                                        #
        #                                                                #
        #     4) child top is on-screen and child bottom is on-screen.   #
        #            +-----------------------+                           #
        #            |  +-------+            |                           #
        #            |  | child |   parent   |                           #
        #            |  +-------+            |                           #
        #            +-----------------------+                           #
        #                                                                #
        # Similarly, by symmetry, four cases for left / right of child.  #
        ##################################################################

        # st, dt, sb, db, sl, dl, sr, dr stand for source_top, destination_top, source_bottom,
        # destination_bottom, source_left, destination_left, source_right, destination_right.
        if ct < 0:
            st = -ct
            dt = 0

            if cb >= h:
                sb = h + st
                db = h
            else:
                sb = child.height
                db = cb
        else:
            st =  0
            dt = ct

            if cb >= h:
                sb = h - dt
                db = h
            else:
                sb = child.height
                db = cb

        if cl < 0:
            sl = -cl
            dl = 0

            if cr >= w:
                sr = w + sl
                dr = w
            else:
                sr = child.width
                dr = cr
        else:
            sl = 0
            dl = cl

            if cr >= w:
                sr = w - dl
                dr = w
            else:
                sr = child.width
                dr = cr

        content[dt: db, dl: dr] = child.content[st: sb, sl: sr]
        self.attrs[dt: db, dl: dr] = child.attrs[st: sb, sl: sr]

    def render(self):
        render_child = self._render_child

        for child in self.children:
            render_child(child)


class Root(Widget):
    """A widget that renders to terminal.
    """
    def __init__(self, env_out):
        self.env_out = env_out
        self.children = [ ]
        self.resize(env_out.get_size())

    def resize(self, dim):
        self.content = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, None, dtype=object)
        self.attrs[:] = NO_ATTRS

        for child in self.children:
            child.update_geometry(dim)

    @property
    def root(self):
        return self

    def render(self):
        self.erase()

        super().render()

        env_out = self.env_out

        # Avoiding attribute lookups.
        goto = env_out.cursor_goto
        set_attr = env_out.set_attributes
        write = env_out.write

        depth = ColorDepth.DEPTH_24_BIT  # FIXME: Temporarily forcing for testing.

        for i, (line, attr_row) in enumerate(zip(self.content, self.attrs)):
            goto(i, 0)

            for char, attr in zip(line, attr_row):
                set_attr(attr, depth)  # TODO: write escape sequences directly or call windows api with windowsattrs directly
                write(char)

        env_out.flush()
