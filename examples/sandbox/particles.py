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
    SLEEP = 0

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
        """
        Stop updating.
        """
        self._update_task.cancel()

    def wake(self):
        """
        Resume updating.
        """
        if self._update_task.done():
            self._update_task = asyncio.create_task(self.update())

    def replace(self, element=None):
        """
        Stop updating and replace with element or Air.
        """
        self.sleep()
        self.wake_neighbors()
        (element or Air)(self.world, self.pos)

    async def update(self):
        step = self.step

        while True:
            step()

            self.LIFETIME -= 1.0

            if self.LIFETIME <= 0.0:
                self.replace()

            try:
                await asyncio.sleep(self.SLEEP)
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
        Default implementation.  Return False.
        """
        return False

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

            density = self.DENSITY

            if (
                neighbor.STATE == State.SOLID and self.STATE != State.LIQUID
                or density > 0 and density <= neighbor_density
                or density < 0 and density >= neighbor_density
            ):
                return False

            self.wake_neighbors()

            neighbor.pos = y, x
            world[y, x] = neighbor

            self.pos = new_y, new_x
            world[new_y, new_x] = self
            return True

        # Fall off the world
        self.replace(Air)
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
            move(dy, 0) or move(dy, dx) or move(dy, -dx)
            or self.STATE != State.SOLID and (
                move(0, dx) or move(0, -dx)
            )
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
    DENSITY = .9
    STATE = State.SOLID
    SLEEP = .1
    LIFETIME = 1000000
    MELT_TIME = float('inf')

    def _move(self, dy, dx):
        if dx == 0:
            return

        return super()._move(dy, dx)

    def replace(self, element=Water):
        super().replace(element)

    def update_neighbor(self, neighbor):
        if self.MELT_TIME == float('inf') and isinstance(neighbor, Water):
            self.MELT_TIME = 15  # Give the snow some time to settle before it descends into the water.
            self.SLEEP = .2

    def step(self):
        self.MELT_TIME -= 1

        if self.MELT_TIME <= 0 and self.DENSITY == .9:
            self.DENSITY = 1.1
            self.LIFETIME = 10

        if random() > .99:
            self.STATE = State.SOLID if self.STATE == State.LIQUID else State.LIQUID

        if self.STATE == State.LIQUID and random() > .99:
            self.replace(Water)
        else:
            super().step()

class Steam(MovingElement):
    LIFETIME = 1000
    COLOR = Color(148, 174, 204)
    DENSITY = -2.0
    STATE = State.GAS

    def replace(self, element=Water):
        super().replace(element)


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
                neighbor.replace(Fire)

            return True

        elif isinstance(neighbor, Air):
            if random() > .989:
                neighbor.replace(Smoke)

        elif isinstance(neighbor, Water):
            if random() > .95:
                neighbor.replace(Steam)

                self.replace()
                return True

            elif random() > .95:
                self.replace(Smoke)
                return True

        elif isinstance(neighbor, Snow):
            if random() > .945:
                neighbor.replace(Water)

        elif isinstance(neighbor, Oil):
            if random() > .92:
                neighbor.sleep()
                fire = Fire(world, neighbor.pos)
                fire.LIFETIME = 25
