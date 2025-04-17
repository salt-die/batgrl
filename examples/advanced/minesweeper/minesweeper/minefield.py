from itertools import product

import cv2
import numpy as np
from batgrl.geometry import rect_slice
from batgrl.text_tools import Cell

from .colors import BORDER, FLAG_COLOR, HIDDEN_SQUARE
from .grid import Grid
from .unicode_chars import FLAG


class Minefield(Grid):
    """A grid that becomes transparent when clicked revealing the counts underneath."""

    def __init__(self, count, minefield, **kwargs):
        super().__init__(
            size=count.shape, is_light=False, is_transparent=True, **kwargs
        )
        self.count = count
        self.minefield = minefield
        self.nmines = minefield.sum()
        self._is_gameover = False

        vs, hs = self.V_SPACING, self.H_SPACING
        v_center, h_center = self.cell_center_indices

        self.canvas["fg_color"] = HIDDEN_SQUARE
        self.canvas["bg_color"] = BORDER
        self.canvas["fg_color"][v_center, h_center] = FLAG_COLOR

        # Build an array whose zero values indicate revealed areas.
        kernel = np.ones((vs + 1, hs + 1), dtype=np.uint8)
        squares = np.zeros(self.size, dtype=np.uint8)
        squares[v_center, h_center] = 1

        self.hidden = cv2.filter2D(squares, -1, kernel, borderType=cv2.BORDER_CONSTANT)
        self.hidden_cells = self.hidden[v_center, h_center]

        self._pressed_cell = self._pressed_button = None

    def on_mouse(self, mouse_event):
        if mouse_event.event_type not in ("mouse_down", "mouse_up"):
            return False

        if not self.collides_point(mouse_event.pos):
            if mouse_event.event_type == "mouse_up" and self._pressed_cell:
                self._release()

            return False

        if mouse_event.event_type == "mouse_down":
            if self._pressed_cell:
                self._release()

            self._pressed_cell = self._cell_from_pos(mouse_event.pos)
            self._pressed_button = mouse_event.button

            if mouse_event.button == "left":
                self._normal_press()
            elif mouse_event.button == "right":
                self._flag_press()
            elif mouse_event.button == "middle":
                self._super_press()
            else:
                return False

        else:  # MOUSE_UP
            if not self._pressed_cell:
                return False

            if self._cell_from_pos(
                mouse_event.pos
            ) == self._pressed_cell and self._pressed_button in (
                "left",
                "middle",
            ):
                self.reveal_cell(
                    self._pressed_cell,
                    reveal_neighbors=self._pressed_button == "middle",
                )

            self._release()

        return True

    def _cell_from_pos(self, mouse_position):
        """Return the cell-coordinates cooresponding to given mouse position."""
        y, x = self.to_local(mouse_position)

        if y == self.height - 1:
            y -= 1

        if x == self.width - 1:
            x -= 1

        return y // self.V_SPACING, x // self.H_SPACING

    def _cell_center(self, cell):
        """Cell center in grid-coordinates."""
        y, x = cell
        vs, hs = self.V_SPACING, self.H_SPACING

        return y * vs + vs // 2, x * hs + hs // 2

    def _cell_slice(self, cell):
        """Return a tuple of slices that indicate a cell's rect in the grid."""
        y, x = cell

        vs, hs = self.V_SPACING, self.H_SPACING
        j, i = y * vs, x * hs

        return slice(j, j + vs + 1), slice(i, i + hs + 1)

    def _recolor_cell(self, cell, fg, bg):
        self.canvas["fg_color"][self._cell_slice(cell)] = fg
        self.canvas["bg_color"][self._cell_slice(cell)] = bg

        u, v = self._cell_center(cell)
        self.canvas["fg_color"][u, v] = FLAG_COLOR

    def _neighbors(self, cell):
        y, x = cell
        h, w = self.minefield.shape

        for j, i in product((-1, 0, 1), repeat=2):
            if j == i == 0:
                continue

            v, u = j + y, i + x
            # Bounds check
            if v < 0 or v >= h or u < 0 or u >= w:
                continue

            yield v, u

    def is_flagged(self, cell):
        return self.chars[self._cell_center(cell)] == FLAG

    def _normal_press(self):
        if not self._is_gameover:
            self.parent.reset_button.update_down()

        cell = self._pressed_cell

        if self.hidden_cells[cell] != 0 and not self.is_flagged(cell):
            self._recolor_cell(cell, BORDER, HIDDEN_SQUARE)

    def _flag_press(self):
        cell = self._pressed_cell

        if self.hidden_cells[cell] != 0:
            is_flagged = self.is_flagged(cell)

            self.chars[self._cell_center(cell)] = " " if is_flagged else FLAG
            self.parent.mines += 1 if is_flagged else -1

    def _super_press(self):
        if not self._is_gameover:
            self.parent.reset_button.update_down()

        cell = self._pressed_cell

        if self.hidden_cells[cell] != 0 and not self.is_flagged(cell):
            self._recolor_cell(cell, BORDER, HIDDEN_SQUARE)

        for neighbor in self._neighbors(cell):
            if self.hidden_cells[neighbor] != 0 and not self.is_flagged(neighbor):
                self._recolor_cell(neighbor, BORDER, HIDDEN_SQUARE)

    def _release(self):
        if not self._is_gameover:
            self.parent.reset_button.update_normal()

        cell = self._pressed_cell

        self._recolor_cell(cell, HIDDEN_SQUARE, BORDER)

        if self._pressed_button == "middle":
            for neighbor in self._neighbors(cell):
                self._recolor_cell(neighbor, HIDDEN_SQUARE, BORDER)

        self._pressed_cell = self._pressed_button = None

    def reveal_cell(self, cell, reveal_neighbors: bool):
        if reveal_neighbors:
            adjacent_flags = sum(map(self.is_flagged, self._neighbors(cell)))

            if self.hidden_cells[cell] == 0 and self.count[cell] != adjacent_flags:
                return

            for neighbor in self._neighbors(cell):
                self.reveal_cell(neighbor, reveal_neighbors=False)

        if self.hidden_cells[cell] == 0 or self.is_flagged(cell):
            return

        if self.minefield[cell]:
            self._game_over(win=False)
            return

        self.hidden[self._cell_slice(cell)] -= 1

        if self.count[cell] == 0:
            for neighbor in self._neighbors(cell):
                self.reveal_cell(neighbor, reveal_neighbors=False)

        if self.hidden_cells.sum() == self.nmines:
            self._game_over(win=True)
            return

    def _game_over(self, win: bool):
        self.hidden[:] = 0
        self._is_gameover = True
        self.parent.game_over(win=win)

    def _render(self, cell, graphics, kind):
        abs_pos = self.absolute_pos
        for pos, size in self._region.rects():
            dst = rect_slice(pos, size)
            src = rect_slice(pos - abs_pos, size)
            visible = self.hidden[src] != 0
            cell.view(Cell)[dst][visible] = self.canvas[src][visible]
