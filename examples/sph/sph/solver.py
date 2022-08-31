import numpy as np


class SPHSolver:
    def __init__(self, nparticles, size):
        self.nparticles = nparticles
        self.resize(size)

        self.H = 1.1
        self.GAS_CONST = 2300.0
        self.REST_DENS = 300.0
        self.VISC = 500.0
        self.MASS = 250.0
        self.DT = .01
        self.GRAVITY = np.array([1e6, 0.0])

    @property
    def H(self):
        return self._H

    @H.setter
    def H(self, H):
        self._H = H
        self.POLY6 = 4.0 / (np.pi * H**8.0)
        self.SPIKY_GRAD = -10.0 / (np.pi * H**5.0)
        self.VISC_LAP = 40.0 / (np.pi * H**5.0)

    def resize(self, size):
        self.size = size
        self.state = np.zeros((self.nparticles, 4), dtype=float)
        self.init_dam()

    def init_dam(self):
        """
        Position particles in a verticle column.
        """
        h, w = self.size
        dam_width = w / 5

        self.state[:] = 0
        positions = self.state[:, :2]

        positions[:] = np.random.random((self.nparticles, 2))
        positions *= h, dam_width
        positions[:, 1] += (w - dam_width) / 2

    def step(self):
        """
        For each particle, compute densities and pressures, then forces, and
        finally integrate to obtain new positions.
        """
        H = self.H
        MASS = self.MASS
        positions    = self.state[:, :2]
        velocities   = self.state[:, 2:4]

        relative_distances = positions[:, None, :] - positions[None, :, :]
        distances_sq = (relative_distances ** 2).sum(axis=-1)
        distances = distances_sq ** .5
        not_neighbors = distances >= H

        # Set density / pressure of all particles.
        strength = (H ** 2 - distances_sq)**3
        strength[not_neighbors] = 0
        densities = MASS * self.POLY6 * strength.sum(axis=-1)
        pressure = self.GAS_CONST * (densities - self.REST_DENS)

        # Calculate forces due to pressure.
        with np.errstate(divide="ignore", invalid="ignore"):
            normals = relative_distances / distances[..., None]
        normals[distances == 0] = 0

        weight = H - distances
        weight[not_neighbors] = 0
        weight[np.diag_indices_from(weight)] = 0

        f_pressure = (
            self.SPIKY_GRAD
            * -normals
            * (pressure[:, None] + pressure[None, :])[..., None] / 2
            * weight[..., None] ** 3
        ).sum(axis=1)

        f_visc = (
            self.VISC
            * self.VISC_LAP
            * (velocities[:, None, :] - velocities[None, :, :])
            * weight[..., None]
        ).sum(axis=1)

        forces = MASS * (f_pressure - f_visc + self.GRAVITY) / densities[:, None]

        # Integrate
        velocities += self.DT * forces / densities[:, None]
        positions += self.DT * velocities

        # Boundary conditions
        h, w = self.size

        ys, xs = positions.T
        vys, vxs = velocities.T

        top = ys < 0
        left = xs < 0
        bottom = ys >= h
        right = xs >= w

        ys[top]    *= -1
        xs[left]   *= -1
        ys[bottom] = 2 * h - ys[bottom]
        xs[right]  = 2 * w - xs[right]

        vys[top]    *= -.5
        vxs[left]   *= -.5
        vys[bottom] *= -.5
        vxs[right]  *= -.5
