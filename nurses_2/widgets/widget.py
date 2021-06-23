from collections.abc import Iterable

import numpy as np

from ..colors import get_color_cache

DEFAULT_ATTR = get_color_cache().color('')


class Widget:
    """
    A generic TUI element.
    """
    def __init__(self, dim, pos=(0, 0), *, is_transparent=False, is_visible=True, parent=None):
        self.top, self.left = pos
        self.is_transparent = is_transparent
        self.is_visible = is_visible

        self.parent = parent
        self.children = [ ]

        self.canvas = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, DEFAULT_ATTR, dtype=object)

    def resize(self, dim):
        """
        Resize canvas. Content is preserved as much as possible.
        """
        old_canvas = self.canvas
        old_attrs = self.attrs

        old_h, old_w = old_canvas.shape
        h, w = dim

        copy_h = min(old_h, h)
        copy_w = min(old_w, w)

        self.canvas = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, DEFAULT_ATTR, dtype=object)

        self.canvas[:copy_h, :copy_w] = old_canvas[:copy_h, :copy_w]
        self.attrs[:copy_h, :copy_w] = old_attrs[:copy_h, :copy_w]

        for child in self.children:
            child.update_geometry(dim)

    def update_geometry(self, parent_dim):
        """
        Update geometry due to a change in parent's size.
        """

    @property
    def dim(self):
        return self.canvas.shape

    @property
    def height(self):
        return self.canvas.shape[0]

    @property
    def width(self):
        return self.canvas.shape[1]

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
        """
        The root widget.
        """
        return self.parent.root

    def add_widget(self, widget):
        """
        Add a child widget.
        """
        self.children.append(widget)
        widget.parent = self
        widget.update_geometry(self.dim)

    def add_widgets(self, *widgets):
        """
        Add multiple child widgets. (If `widgets` is an iterable it must be only argument.)
        """
        if len(widgets) == 1 and isinstance(widgets[0], Iterable):
            widgets = widgets[0]

        for widget in widgets:
            self.add_widget(widget)

    def remove_widget(self, widget):
        """
        Remove widget.
        """
        self.children.remove(widget)
        widget.parent = None

    def pull_to_front(self, widget):
        """
        Move widget to end of widget stack so that it is drawn last.
        """
        self.children.remove(widget)
        self.children.append(widget)

    def walk_from_root(self):
        """
        Yield all descendents of the root widget.
        """
        yield from self.root.walk()

    def walk(self):
        """
        Yield self and all descendents.
        """
        yield self

        for child in widget.children:
            yield from child.walk()

    def _render_child(self, child):
        """
        Render child and paint child's canvas into our own.
        """
        canvas = self.canvas
        h, w = canvas.shape

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

        canvas[dt: db, dl: dr] = child.canvas[st: sb, sl: sr]
        self.attrs[dt: db, dl: dr] = child.attrs[st: sb, sl: sr]

    def render(self):
        """
        Paint canvas.
        """
        render_child = self._render_child

        for child in self.children:
            render_child(child)


class Root(Widget):
    """
    A widget that renders to terminal.
    """
    def __init__(self, env_out):
        self.env_out = env_out
        self.children = [ ]

        self.resize(env_out.get_size())

    def resize(self, dim):
        """
        Resize canvas. Last render is erased.
        """
        self.canvas = np.full(dim, " ", dtype=object)
        self.attrs = np.full(dim, DEFAULT_ATTR, dtype=object)
        self._last_canvas = self.canvas.copy()
        self._last_attrs = self.attrs.copy()

        self.erase_screen()

        for child in self.children:
            child.update_geometry(dim)

    @property
    def root(self):
        return self

    def render(self):
        """
        Paint canvas.  Render to terminal.
        """
        # Swap canvas with last render.
        self.canvas, self._last_canvas = self._last_canvas, self.canvas
        self.attrs, self._last_attrs = self._last_attrs, self.attrs

        canvas = self.canvas
        attrs = self.attrs

        last_canvas = self._last_canvas
        last_attrs = self._last_attrs

        # Erase canvas.
        canvas[:] = " "
        attrs[:] = DEFAULT_ATTR

        # Paint canvas.
        super().render()

        env_out = self.env_out

        # Avoiding attribute lookups.
        goto = env_out.cursor_goto
        set_attr = env_out.set_attr_raw
        write_raw = env_out.write_raw
        reset = env_out.reset_attributes

        # Only write the difs.
        for y, x in np.argwhere((last_canvas != canvas) | (last_attrs != attrs)):
            goto(y, x)
            set_attr(attrs[y, x])
            write_raw(canvas[y, x])
            reset()

        env_out.flush()

    def erase_screen(self):
        """
        Erase screen.
        """
        env_out = self.env_out

        env_out.reset_attributes()
        env_out.erase_screen()
        env_out.hide_cursor()
        env_out.flush()
