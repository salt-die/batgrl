import numpy as np
from scipy.spatial import KDTree

from nurses_2.data_structures import Size


class SPHSolver:
    GRAVITY = .007
    REST_DENS = 300.0
    GAS_CONST = 2000.0
    H = 16.0
    MASS = 2.5
    VISC = 200.0
    POLY6 = 4.0 / (np.pi * H**8.0)
    SPIKY_GRAD = -10.0 / (np.pi * H**5.0)
    VISC_LAP = 40.0 / (np.pi * H**5.0)
    BOUND_DAMPING = -.5

    def __init__(self, size: Size, nparticles=1000):
        self.size = size
        self.state = np.zeros((nparticles, 8))
        self.init_dam()

    @property
    def positions(self):
        return self.state[:, :2]

    @property
    def velocities(self):
        return self.state[:, 2:4]

    @property
    def acceleration(self):
        return self.state[:, 4:6]

    @property
    def densities(self):
        return self.state[:, 6]

    @property
    def pressure(self):
        return self.state[:, 7]

    def init_dam(self):
        """
        Position particles in a verticle column.
        """
        height, width = self.size
        dam_width = width / 5

        self.positions[:] = np.random.random((self.state.shape[0], 2))
        self.positions *= height, dam_width
        self.positions[:, 1] += dam_width

    def step(self):
        """
        For each particle, compute densities and pressures, then forces, and
        finally integrate to obtain new positions.
        """
        pairs = KDTree(self.positions).query_pairs(self.H)
        self._density_pressure(pairs)
        self._forces(pairs)
        self._integrate()

    def _density_pressure(self, pairs):
        MASS = self.MASS
        POLY6 = self.POLY6
        H = self.H

        positions = self.positions
        densities = self.densities

        norm = np.linalg.norm

        densities[:] = 0.0

        for i, j in pairs:
            density = MASS * POLY6 * (H - norm(positions[i] - positions[j]))**3
            densities[i] += density
            densities[j] += density

        self.pressure[:] = self.GAS_CONST * (densities - self.REST_DENS)

    def _forces(self, pairs):
        positions = self.positions
        velocities = self.velocities
        acceleration = self.acceleration
        density = self.densities
        pressure = self.pressure

        MASS = self.MASS
        SPIKY_GRAD = self.SPIKY_GRAD
        H = self.H
        VISC = self.VISC
        VISC_LAP = self.VISC_LAP

        norm = np.linalg.norm

        acceleration[:] = 0.0

        for i, j in pairs:
            relative = positions[i] - positions[j]
            distance = norm(relative)
            normal = relative / distance

            strength = H - distance

            force_ij = -normal * MASS * (pressure[i] + pressure[j]) * SPIKY_GRAD * strength**3 * .5
            visc_ij = VISC * MASS * (velocities[j] - velocities[i]) * VISC_LAP * strength

            acceleration[i] += force_ij / density[j]
            acceleration[i] += visc_ij / density[j]

            acceleration[j] += -force_ij / density[i]
            acceleration[j] += -visc_ij / density[j]

        acceleration += self.GRAVITY * MASS / density

    def _integrate(self):
        velocities = self.velocities
        positions = self.positions

        velocities += self.acceleration / self.densities
        positions += self.velocities

        # Move out-of-bounds particles back in-bounds.
        oob = (positions < 0) | (positions > self.size)

        positions[oob] *= -1
        velocities[oob] *= self.BOUND_DAMPING
