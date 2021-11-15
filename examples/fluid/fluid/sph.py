import numpy as np
from scipy.spatial import KDTree

H = .49
GAS_CONST = 200.0
REST_DENS = 200.0
POLY6 = 1.0 / (np.pi * H**8.0)
VISC = 5000.0 / (np.pi * H**5.0)
SPIKY_GRAD = -5.0 / (np.pi * H**5.0)
GRAVITY = 40.0

# ? A mysterious negative velocity bias is keeping Solver from settling.


class SPHSolver:
    def __init__(self, size, nparticles=1000):
        self.nparticles = nparticles
        self.resize(size)

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
        density = POLY6 * strengths_cubed

        densities[:] = REST_DENS
        densities[js] += density
        densities[ks] += density

        pressure[:] = GAS_CONST * (densities - REST_DENS)

        # Update forces
        pressure_jk = (
            SPIKY_GRAD
            * relatives
            / distances[:, None]
            * (pressure[ks] + pressure[js])[:, None]
            * strengths_cubed[:, None]
        )

        viscs_jk = (
            VISC
            * (velocities[ks] - velocities[js])
            * strengths[:, None]
         )

        total = pressure_jk + viscs_jk

        acceleration[:, 0] += GRAVITY
        acceleration[js] += total
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
