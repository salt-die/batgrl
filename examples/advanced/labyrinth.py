"""
You're stuck in the Labyrinth, a maze that re-arranges itself as you try to escape!

Press arrow keys to move. Requires `networkx`.
"""
import asyncio
from itertools import cycle
from random import choice, random

import numpy as np
import networkx as nx

from nurses_2.app import run_widget_as_app
from nurses_2.colors import gradient, AColor, AWHITE
from nurses_2.widgets.graphic_widget import GraphicWidget

GREEN = AColor.from_hex("0bbf23")
BLUE = AColor.from_hex("0b38bf")
PLAYER_GRADIENT = cycle(gradient(BLUE, AWHITE, 50) + gradient(AWHITE, BLUE, 50))

def _path_yx(a, b):
    """
    Given two nodes in a maze, return the coordinate of the path that connects them.
    """
    ay, ax = a
    by, bx = b
    return ay + by + 1, ax + bx + 1


class Labyrinth(GraphicWidget):
    def on_add(self):
        self._new_level_task = asyncio.create_task(asyncio.sleep(0))  # dummy task
        self._player_task = asyncio.create_task(self._update_player())
        self._reconfigure_task = asyncio.create_task(self._step_reconfigure())
        self.on_size()
        super().on_add()

    def on_remove(self):
        super().on_remove()
        self._player_task.cancel()
        self._new_level_task.cancel()
        self._reconfigure_task.cancel()

    def on_size(self):
        h, w = self._size
        self.texture = np.zeros((2 * h, w, 4), dtype=np.uint8)

        # Creating new level is intensive. To prevent lock-up when resizing terminal,
        # defer creation for a small amount of time.
        self._suspend_tasks = True
        self._new_level_task.cancel()
        self._new_level_task = asyncio.create_task(self._new_level_soon())

    async def _new_level_soon(self):
        try:
            await asyncio.sleep(.1)
        except asyncio.CancelledError:
            pass
        else:
            self.new_level()

    def new_level(self):
        self.player = 1, 0
        self._suspend_tasks = False

        h, w = self._size
        h *= 2

        self.grid_graph = gg = nx.grid_graph(((w - 1) // 2, (h - 1) // 2))
        for e in gg.edges:
            gg.edges[e]['weight'] = random()

        self.maze = maze = nx.algorithms.minimum_spanning_tree(gg)
        self.nodes = list(self.maze.nodes)

        self._texture_gradient = np.array(
            [gradient(color, BLUE, w) for color in gradient(GREEN, BLUE, h)],
            dtype=np.uint8,
        )

        self.texture[:] = self._texture_gradient
        self.texture[-1] = self.texture[:, w - 1 + w % 2:] = 0  # Extra line of pixels removed.
        self.texture[(1, -3), (0, w % 2 - 2)] = 0  # Ends of maze.

        for y, x in maze.nodes:
            self.texture[2 * y + 1, 2 * x + 1] = 0
        for u, v in maze.edges:
            self.texture[_path_yx(u, v)] = 0

    async def _update_player(self):
        while True:
            if not self._suspend_tasks:
                self.texture[self.player] = next(PLAYER_GRADIENT)
            await asyncio.sleep(.03)

    async def _step_reconfigure(self):
        while True:
            if not self._suspend_tasks:
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

    def on_key_press(self, key_press_event):
        match key_press_event.key:
            case "up":
                dy, dx = -1, 0
            case "left":
                dy, dx = 0, -1
            case "right":
                dy, dx = 0, 1
            case "down":
                dy, dx = 1, 0
            case _:
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


run_widget_as_app(Labyrinth(size_hint=(1.0, 1.0)))
