from abc import ABC, abstractmethod
import asyncio
from enum import Enum
from itertools import cycle
from random import random

from nurses_2.colors import Color


class State(Enum):
    """
    Element states.
    """
    GAS = "GAS"
    LIQUID = "LIQUID"
    SOLID = "SOLID"


class CycleColorBehavior:
    """
    Cycles through several colors for an element.

    Notes
    -----
    `COLORS` should be an infinite iterator.
    """
    COLORS = None  # itertools.cycle

    def step(self):
        self.COLOR = next(self.COLORS)
        super().step()


class Element(ABC):
    COLOR = None
    DENSITY = None
    STATE = None
    LIFETIME = float('inf')

    all_elements = { }

    def __init_subclass__(cls):
        if hasattr(cls, 'COLORS'):
            cls.COLOR = next(cls.COLORS)

        if all(getattr(cls, attr) is not None for attr in ("COLOR", "DENSITY", "STATE")):
            cls.all_elements[cls.__name__] = cls

    def __init__(self, world, pos):
        self.world = world
        self.pos = pos

        self.world[pos] = self
        self._update_task = asyncio.create_task(self.update())

    def sleep(self):
        self._update_task.cancel()

    def wake(self):
        self._update_task.cancel()
        self._update_task = asyncio.create_task(self.update())

    async def update(self):
        step = self.step

        while True:
            step()

            self.LIFETIME -= 1.0

            if self.LIFETIME <= 0.0:
                Air(self.world, self.pos)
                return

            try:
                await asyncio.sleep(0)
            except asyncio.CancelledError:
                return

    def neighbors(self):
        """
        Yield all neighbors.
        """
        world = self.world
        h, w = world.shape
        y, x = self.pos
        deltas = (
            (-1, -1),
            (-1,  0),
            (-1,  1),
            ( 0, -1),
            ( 0,  1),
            ( 1, -1),
            ( 1,  0),
            ( 1,  1),
        )

        for dy, dx in deltas:
            if 0 <= y + dy < h and 0 <= x + dx < w:
                yield world[y + dy, x + dx]

    def wake_neighbors(self):
        """
        Wake all neighbors.
        """
        for neighbor in self.neighbors():
            neighbor.wake()

    def update_neighbors(self):
        """
        Update all neighbors or until `update_neighbor` returns True.
        """
        for neighbor in self.neighbors():
            if self.update_neighbor(neighbor):
                return True

        return False

    @abstractmethod
    def update_neighbor(self, neighbor):
        """
        Update neighbor.

        Return True to stop updating.
        """
        pass

    @abstractmethod
    def step(self):
        """
        Single step of an element's update.
        """
        self.update_neighbors()


class InertElement(Element):
    """
    Base for inert elements.
    """
    def update_neighbor(self, neighbor):
        """
        Do nothing.
        """

    def step(self):
        """
        Cancel updating.
        """
        self._update_task.cancel()


class MovingElement(Element):
    """
    Base for moving elements.
    """
    def _move(self, dy, dx):
        world = self.world
        h, w = world.shape

        y, x = self.pos

        new_y = y + dy
        new_x = x + dx

        if 0 <= new_y < h and 0 <= new_x < w:
            neighbor = world[new_y, new_x]
            neighbor_density = neighbor.DENSITY
            neighbor_state = neighbor.STATE

            density = self.DENSITY
            state = self.STATE

            if (
                neighbor_state == State.SOLID and state != State.LIQUID
                or density < 0 and neighbor_density <= density
                or density > 0 and neighbor_density >= density
            ):
                return False

            self.wake_neighbors()

            neighbor.pos = y, x
            world[y, x] = neighbor

            self.pos = new_y, new_x
            world[new_y, new_x] = self
            return True

        # Fall off the world
        world[y, x] = Air(world, (y, x))
        self._update_task.cancel()
        return True

    def update_neighbor(self, neighbor):
        """
        Default implementation.  Return False.
        """
        return False

    def step(self):
        if self.update_neighbors():
            return True

        move = self._move
        dy = 1 if self.DENSITY > 0 else -1  # Air has a density of 0, so less than this and element will "fall" up.
        dx = 2 * round(random()) - 1

        if not (
            move(dy, 0)
            or move(dy, dx)
            or move(dy, -dx)
            or self.STATE != State.SOLID and (
                move(0, dx) or move(0, -dx)
            )  # Only fluids "slide".
        ) and self.LIFETIME == float('inf'):  # Elements with finite lifetime don't sleep.
            self.sleep()


################
# Particle Zoo #
################

class Air(InertElement):
    COLOR = Color(25, 25, 25)
    DENSITY = 0.0
    STATE = State.GAS


class Stone(InertElement):
    COLOR = Color(120, 110, 120)
    DENSITY = 100.0
    STATE = State.SOLID


class Wood(InertElement):
    COLOR = Color(81, 42, 6)
    DENSITY = 80.0
    STATE = State.SOLID


class Sand(MovingElement):
    COLOR = Color(150, 100, 50)
    DENSITY = 50.0
    STATE = State.SOLID


class Water(MovingElement):
    COLOR = Color(20, 100, 170)
    DENSITY = 1.0
    STATE = State.LIQUID


class Snow(MovingElement):
    COLOR = Color(200, 200, 250)
    DENSITY = .8
    STATE = State.SOLID

    def step(self):
        if random() > .99:
            self.STATE = State.SOLID if self.STATE == State.LIQUID else State.LIQUID

        if self.STATE == State.LIQUID and random() > .99:
            self.sleep()
            water = Water(self.world, self.pos)
            water.wake_neighbors()
        else:
            super().step()


class Steam(MovingElement):
    LIFETIME = 1000
    COLOR = Color(148, 174, 204)
    DENSITY = -2.0
    STATE = State.GAS

    def sleep(self):
        super().sleep()
        Water(self.world, self.pos)


class Oil(MovingElement):
    COLOR = Color(56, 54, 33)
    DENSITY = .5
    STATE = State.LIQUID


class Smoke(MovingElement):
    LIFETIME = 850
    COLOR = Color(140, 140, 140)
    DENSITY = -1.0
    STATE = State.GAS


class Fire(CycleColorBehavior, MovingElement):
    LIFETIME = 1000
    COLORS = cycle((
        Color(186, 105, 29),
        Color(244, 146, 53),
        Color(229, 179, 52),
    ))
    DENSITY = .1
    STATE = State.SOLID

    def update_neighbor(self, neighbor):
        world = self.world

        if isinstance(neighbor, Wood):
            if random() > .99:
                Fire(world, neighbor.pos)
            return True

        elif isinstance(neighbor, Air):
            if random() > .989:
                Smoke(world, neighbor.pos)

        elif isinstance(neighbor, Water):
            if random() > .95:
                neighbor.sleep()
                Steam(world, neighbor.pos)

                self.LIFETIME = 0
                self.sleep()
                Air(world, self.pos)

                return True

        elif isinstance(neighbor, Snow):
            if random() > .945:
                neighbor.sleep()
                Water(world, neighbor.pos)

                self.LIFETIME = 0
                self.sleep()
                Air(world, self.pos)

                return True

        elif isinstance(neighbor, Oil):
            if random() > .92:
                neighbor.sleep()
                fire = Fire(world, neighbor.pos)
                fire.LIFETIME = 25
