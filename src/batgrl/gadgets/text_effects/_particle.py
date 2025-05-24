from collections.abc import Iterator
from dataclasses import dataclass
from typing import Self

from ...geometry.motion import Coord, HasPosProp
from ...text_tools import Cell0D
from ..text_field import Point, TextParticleField


@dataclass
class Particle(HasPosProp):
    """
    A wrapper around an index into a text particle field's particle arrays.

    Parameters
    ----------
    field : TextParticleField
        The field which the particle belongs.
    index : int
        The index of the particle in the field.

    Attributes
    ----------
    field : TextParticleField
        The field which the particle belongs.
    index : int
        The index of the particle in the field.
    cell : Cell0D
        The particle's cell.
    pos : Point
        The particle's position.

    Methods
    -------
    iter_from_field(field)
        Yield all particles from a text particle field.
    """

    field: TextParticleField
    index: int

    @property
    def cell(self) -> Cell0D:
        """The particle's cell."""
        return self.field.particle_cells[self.index]

    @cell.setter
    def cell(self, cell: Cell0D):
        self.field.particle_cells[self.index] = cell

    @property
    def pos(self) -> Point:
        """The particle's position."""
        return Point(*self.field.particle_coords[self.index].tolist())

    @pos.setter
    def pos(self, pos: Coord):
        self.field.particle_coords[self.index] = pos

    @classmethod
    def iter_from_field(cls, field: TextParticleField) -> Iterator[Self]:
        """Yield all particles from a text particle field."""
        for i in range(len(field.particle_coords)):
            yield cls(field, i)
