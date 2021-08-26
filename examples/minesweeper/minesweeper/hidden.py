import numpy as np
from scipy.ndimage import convolve

from nurses_2.mouse import MouseButton, MouseEventType
from nurses_2.widgets.widget import overlapping_region
from nurses_2.widgets.behaviors.button_behavior import ButtonStates

from .colors import *
from .grid import Grid

FLAG = "⚑"


class Hidden(Grid):
    def __init__(self, size, **kwargs):
        super().__init__(
            size=size,
            is_light=False,
            default_color_pair=HIDDEN,
            **kwargs,
        )
        vs, hs = self.V_SPACING, self.H_SPACING

        self.colors[vs//2::vs, hs//2::hs, :3] = FLAG_COLOR

        # Build an array whose zero values indicate revealed areas.
        kernel = np.ones((vs + 1, hs + 1))
        squares = np.zeros(self.size, dtype=int)
        squares[vs//2::vs, hs//2::hs] = 1

        self.hidden = convolve(squares, kernel, mode="constant")

        self.state = ButtonStates.NORMAL
        self._last_cell = 0, 0

    def on_click(self, mouse_event):
        if mouse_event.event_type == MouseEventType.MOUSE_DOWN:
            if (
                self.state == ButtonStates.NORMAL
                and self.collides_coords(mouse_event.position)
            ):
                if mouse_event.button == MouseButton.LEFT:
                    self._normal_press(mouse_event.position)
                elif mouse_event.button == MouseButton.RIGHT:
                    self._flag_press(mouse_event.position)
                else:
                    return False

                return True

            self._release()

        elif mouse_event.event_type == MouseEventType.MOUSE_UP:
            if (
                self.state == ButtonStates.DOWN
                and self.is_same_cell(mouse_event.position)
            ):
                self._release()
                self.reveal_cell(self._last_cell)

                return True

            self._release()

    def _cell(self, mouse_position):
        y, x = self.absolute_to_relative_coords(mouse_position)

        if y == self.height - 1:
            y -= 1

        if x == self.width - 1:
            x -= 1

        vs, hs = self.V_SPACING, self.H_SPACING

        return y - (y % vs), x - (x % hs)

    def is_same_cell(self, mouse_position):
        return self._cell(mouse_position) == self._last_cell

    def is_cell_hidden(self, cell):
        y, x = cell
        vs, hs = self.V_SPACING, self.H_SPACING
        return (self.hidden[y: y + vs + 1, x: x + hs + 1] != 0).all()

    def is_cell_flagged(self, cell):
        y, x = cell
        vs, hs = self.V_SPACING, self.H_SPACING

        return self.canvas[y + vs // 2, x + hs // 2] == FLAG

    def recolor_cell(self, cell, color_pair):
        y, x = cell
        vs, hs = self.V_SPACING, self.H_SPACING

        self.colors[y: y + vs + 1, x: x + hs + 1] = color_pair
        self.colors[y + vs // 2, x + hs // 2, :3] = FLAG_COLOR

    def _normal_press(self, mouse_position):
        self._last_cell = cell = self._cell(mouse_position)

        vs, hs = self.V_SPACING, self.H_SPACING

        if self.is_cell_flagged(cell):
            return

        if self.is_cell_hidden(cell):
            self.recolor_cell(cell, HIDDEN_REVERSED)
            self.state = ButtonStates.DOWN

    def _flag_press(self, mouse_position):
        y, x = cell = self._cell(mouse_position)

        if self.is_cell_hidden(cell):
            vs, hs = self.V_SPACING, self.H_SPACING
            v, u = y + vs // 2, x + hs // 2

            if self.is_cell_flagged(cell):
                self.canvas[v, u] = " "
            else:
                self.canvas[v, u] = FLAG

    def _release(self):
        self.recolor_cell(self._last_cell, HIDDEN)
        self.state = ButtonStates.NORMAL

    def reveal_cell(self, cell):
        if self.is_cell_hidden(cell):
            y, x = cell
            vs, hs = self.V_SPACING, self.H_SPACING
            self.hidden[y: y + vs + 1, x: x + hs + 1] -= 1

    def render(self, canvas_view, colors_view, rect):
        t, l, b, r, _, _ = rect

        index_rect = slice(t, b), slice(l, r)
        source = self.canvas[index_rect]
        visible = self.hidden != 0

        canvas_view[visible] = source[visible]
        colors_view[visible] = self.colors[index_rect][visible]

        overlap = overlapping_region

        for child in self.children:
            if not child.is_visible or not child.is_enabled:
                continue

            if region := overlap(rect, child):
                dest_slice, child_rect = region
                child.render(canvas_view[dest_slice], colors_view[dest_slice], child_rect)
