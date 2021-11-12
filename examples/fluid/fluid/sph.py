import numpy as np

from nurses_2.data_structures import Size


class SPHSolver:
    GRAVITY = .007
    REST_DENS = 300.0
    GAS_CONST = 2000.0
    H = 16.0
    HSQ = H**2
    MASS = 2.5
    VISC = 200.0
    POLY6 = 4.0 / (np.pi * H**8.0)
    SPIKY_GRAD = -10.0 / (np.pi * H**5.0)
    VISC_LAP = 40.0 / (np.pi * H**5.0)
    EPS = H
    BOUND_DAMPING = -.5

    def __init__(self, bounds: Size, nparticles=1000):
        self.height, self.width = bounds
        self.state = np.zeros((nparticles, 8), dtype=float)

        self._differences = np.zeros((nparticles, nparticles, 2))
        self._pow_buf = np.zeros_like(self._differences)

        self._distances = np.zeros((nparticles, nparticles))
        self._sqr_buffer = np.zeros_like(self._distances)

    def init_dam(self):
        """
        Position particles in a verticle column.
        """

    def step(self):
        """
        For each particle, compute densities and pressures, then forces, and
        finally integrate to obtain new positions.
        """
        HSQ = self.HSQ
        MASS = self.MASS
        POLY6 = self.POLY6
        REST_DENS = self.REST_DENS
        GAS_CONST = self.GAS_CONST

        state = self.state

        positions = state[:, :2]
        velocities = state[:, 2:4]
        forces = state[:, 4:6]
        rho = state[:, 6]
        p = state[:, 7]

        # Distances
        ###########

        # Every pairwise combination of distances is computed.
        # This could be optimized with a line-sweep or a tree-like data structure.
        differences = np.subtract(positions[None], positions[:, None], out=self._differences)
        pow_buf = np.power(differences, 2, out=self._pow_buffer)

        distances = pow_buf.sum(axis=-1, out=self._distances)
        distances[np.tril_indices_from(distances)] = 0
        distances[distances >= HSQ] = 0

        # Density and pressure
        ######################

        # (HSQ - distances)**3.0
        _sqr_buffer = np.subtract(HSQ, distances, out=self._sqr_buffer)
        np.power(distances, 3.0, out=_sqr_buffer)

        rho[:] = _sqr_buffer.sum(axis=-1)
        rho *= MASS * POLY6

        np.subtract(rho, REST_DENS, out=p)
        p *= GAS_CONST

        # Forces
        ########
        np.sqrt(distances, out=distances)

        with np.errstate(divide="ignore", invalid="ignore"):
            normals = np.divide(differences, distances, out=differences)


        """
        for (auto &pi : particles)
        {
            Vector2d fpress(0.f, 0.f);
            Vector2d fvisc(0.f, 0.f);
            for (auto &pj : particles)
            {
                if (&pi == &pj)
                {
                    continue;
                }

                Vector2d rij = pj.x - pi.x;
                float r = rij.norm();

                if (r < H)
                {
                    fpress += -rij.normalized() * MASS * (pi.p + pj.p) / (2.f * pj.rho) * SPIKY_GRAD * pow(H - r, 3.f);
                    fvisc += VISC * MASS * (pj.v - pi.v) / pj.rho * VISC_LAP * (H - r);
                }
            }
            Vector2d fgrav = G * MASS / pi.rho;
            pi.f = fpress + fvisc + fgrav;
        """

        # Integrate
        """
        for (auto &p : particles)
        {
            p.v += DT * p.f / p.rho;
            p.x += DT * p.v;

            if (p.x(0) - EPS < 0.f)
            {
                p.v(0) *= BOUND_DAMPING;
                p.x(0) = EPS;
            }
            if (p.x(0) + EPS > VIEW_WIDTH)
            {
                p.v(0) *= BOUND_DAMPING;
                p.x(0) = VIEW_WIDTH - EPS;
            }
            if (p.x(1) - EPS < 0.f)
            {
                p.v(1) *= BOUND_DAMPING;
                p.x(1) = EPS;
            }
            if (p.x(1) + EPS > VIEW_HEIGHT)
            {
                p.v(1) *= BOUND_DAMPING;
                p.x(1) = VIEW_HEIGHT - EPS;
            }
        }
        """
