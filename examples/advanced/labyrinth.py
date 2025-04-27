# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "networkx",
# ]
# ///
"""
You're stuck in the Labyrinth, a maze that re-arranges itself as you try to escape.

Press arrow keys to move. Requires `networkx`.
"""

import asyncio
from itertools import cycle
from random import choice, random

import networkx as nx
import numpy as np
from batgrl.app import run_gadget_as_app
from batgrl.colors import AWHITE, AColor, gradient
from batgrl.gadgets.graphics import Graphics, scale_geometry

GREEN = AColor.from_hex("0bbf23")
BLUE = AColor.from_hex("0b38bf")
PLAYER_GRADIENT = cycle(gradient(BLUE, AWHITE, n=50) + gradient(AWHITE, BLUE, n=50))


def _path_yx(a, b):
    """
    Given two nodes in a maze, return the coordinate of the path that connects
    them.
    """
    ay, ax = a
    by, bx = b
    return ay + by + 1, ax + bx + 1


class Labyrinth(Graphics):
    _new_level_task = None
    _player_task = None
    _reconfigure_task = None

    def on_add(self):
        super().on_add()
        if self._player_task is not None:
            self._player_task.cancel()
        if self._reconfigure_task is not None:
            self._reconfigure_task.cancel()
        if self._new_level_task is not None:
            self._new_level_task.cancel()
        self.new_level()

    def on_remove(self):
        super().on_remove()
        if self._new_level_task is not None:
            self._new_level_task.cancel()
        if self._player_task is not None:
            self._player_task.cancel()
        if self._reconfigure_task is not None:
            self._reconfigure_task.cancel()

    def on_size(self):
        h, w = scale_geometry(self._blitter, self._size)
        self.texture = np.zeros((h, w, 4), dtype=np.uint8)

        if self.root is None:
            return
        # Creating new level is intensive. To prevent lock-up when resizing terminal,
        # defer creation for a small amount of time.
        if self._player_task is not None:
            self._player_task.cancel()
        if self._reconfigure_task is not None:
            self._reconfigure_task.cancel()
        if self._new_level_task is not None:
            self._new_level_task.cancel()
        self._new_level_task = asyncio.create_task(self._new_level_soon())

    async def _new_level_soon(self):
        await asyncio.sleep(0.1)
        self.new_level()

    def new_level(self):
        self.player = 1, 0
        if self._player_task is not None:
            self._player_task.cancel()
        self._player_task = asyncio.create_task(self._update_player())
        if self._reconfigure_task is not None:
            self._reconfigure_task.cancel()
        self._reconfigure_task = asyncio.create_task(self._step_reconfigure())

        h, w = scale_geometry(self._blitter, self._size)
        self.grid_graph = gg = nx.grid_graph(((w - 1) // 2, (h - 1) // 2))
        for e in gg.edges:
            gg.edges[e]["weight"] = random()

        self.maze = maze = nx.algorithms.minimum_spanning_tree(gg)
        self.nodes = list(self.maze.nodes)

        self._texture_gradient = np.array(
            [gradient(color, BLUE, n=w) for color in gradient(GREEN, BLUE, n=h)],
            dtype=np.uint8,
        )

        self.texture[:] = self._texture_gradient
        self.texture[-1] = self.texture[:, w - 1 + w % 2 :] = (
            0  # Extra line of pixels removed.
        )
        self.texture[(1, -3), (0, w % 2 - 2)] = 0  # Ends of maze.

        for y, x in maze.nodes:
            self.texture[2 * y + 1, 2 * x + 1] = 0
        for u, v in maze.edges:
            self.texture[_path_yx(u, v)] = 0

    async def _update_player(self):
        while True:
            self.texture[self.player] = next(PLAYER_GRADIENT)
            await asyncio.sleep(0.03)

    async def _step_reconfigure(self):
        while True:
            self._reconfigure_maze()
            await asyncio.sleep(1)

    def _reconfigure_maze(self):
        u = choice(self.nodes)
        uy, ux = u
        if self.player == (2 * uy + 1, 2 * ux + 1):
            return

        if neighbors := list(self.grid_graph[u].keys() - self.maze[u].keys()):
            v = choice(neighbors)

            self.maze.add_edge(u, v)
            self.texture[_path_yx(u, v)] = 0

            a, b = choice(nx.find_cycle(self.maze, u))
            self.maze.remove_edge(a, b)
            yx = _path_yx(a, b)
            self.texture[yx] = self._texture_gradient[yx]

    def on_key(self, key_event):
        if key_event.key == "up":
            dy, dx = -1, 0
        elif key_event.key == "left":
            dy, dx = 0, -1
        elif key_event.key == "right":
            dy, dx = 0, 1
        elif key_event.key == "down":
            dy, dx = 1, 0
        else:
            return False

        y, x = self.player
        py, px = y + dy, x + dx

        w = self.width
        if px == w - 1 + w % 2:
            self.new_level()
        elif px >= 0 and (self.texture[py, px] == 0).all():
            self.texture[y, x] = 0
            self.texture[py, px] = next(PLAYER_GRADIENT)
            self.player = py, px

        return True


if __name__ == "__main__":
    run_gadget_as_app(
        Labyrinth(size_hint={"height_hint": 1.0, "width_hint": 1.0}), title="Labyrinth"
    )
