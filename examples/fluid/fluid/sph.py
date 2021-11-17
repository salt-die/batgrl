import numpy as np
from scipy.spatial import KDTree


class SPHSolver:
    def __init__(self, size, nparticles=1000):
        self.nparticles = nparticles
        self.resize(size)

        self._H = .49
        self.GAS_CONST = 200.0
        self.REST_DENS = 200.0
        self.POLYF = 1.0
        self.VISCF = 5000.0
        self.SPIKYF = -5.0
        self.GRAVITY = 40.0

    @property
    def H(self):
        return self._H

    @H.setter
    def H(self, value):
        self._H = value
        self.POLY6 = self._POLYF / (np.pi * value**8.0)
        self.VISC = self._VISCF / (np.pi * value**5.0)
        self.SPIKY_GRAD = self._SPIKYF / (np.pi * value**5.0)

    @property
    def POLYF(self):
        return self._POLYF

    @POLYF.setter
    def POLYF(self, value):
        self._POLYF = value
        self.POLY6 = value / (np.pi * self.H**8.0)

    @property
    def VISCF(self):
        return self._VISCF

    @VISCF.setter
    def VISCF(self, value):
        self._VISCF = value
        self.VISC = value / (np.pi * self.H**5.0)

    @property
    def SPIKYF(self):
        return self._SPIKYF

    @SPIKYF.setter
    def SPIKYF(self, value):
        self._SPIKYF = value
        self.SPIKY_GRAD = value / (np.pi * self.H**5.0)

    def resize(self, size):
        self.size = size
        self.state = np.zeros((self.nparticles, 8), dtype=float)
        self.init_dam()

    def init_dam(self):
        """
        Position particles in a verticle column.
        """
        h, w = self.size
        dam_width = w / 5

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
        REST_DENS = self.REST_DENS

        state = self.state
        positions    = state[:, :2]
        velocities   = state[:, 2:4]
        acceleration = state[:, 4:6]
        densities    = state[:, 6]
        pressure     = state[:, 7]

        js, ks = KDTree(positions, balanced_tree=False).query_pairs(H, output_type='ndarray').T

        relatives = positions[ks] - positions[js]
        distances = np.linalg.norm(relatives, axis=-1)

        strengths = H - distances
        strengths_cubed = strengths ** 3

        # Update density / pressure
        density = self.POLY6 * strengths_cubed

        densities[:] = REST_DENS
        densities[js] += density
        densities[ks] += density

        pressure[:] = self.GAS_CONST * (densities - REST_DENS)

        # Update forces
        pressure_jk = (
            self.SPIKY_GRAD
            * relatives
            / distances[:, None]
            * (pressure[ks] + pressure[js])[:, None]
            * strengths_cubed[:, None]
        )

        viscs_jk = (
            self.VISC
            * (velocities[ks] - velocities[js])
            * strengths[:, None]
        )

        total = pressure_jk + viscs_jk

        acceleration[:, 0] += self.GRAVITY
        acceleration[js] += total

        # `-= total` isn't correct. It should be `+= pressure_jk - viscs_jk`,
        # but this keeps the solver from settling, so it looks cooler!
        # If corrected, constants need to be updated.
        acceleration[ks] -= total

        acceleration /= densities[:, None]

        # Integrate
        velocities += acceleration / densities[:, None]
        positions += velocities

        acceleration[:] = 0.0  # Reset forces

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
