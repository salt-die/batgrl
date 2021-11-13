from collections import namedtuple
import numpy as np

from .data_structures import Rect, Particle, QuadTree


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

    def __init__(self, extent: Rect, nparticles=1000):
        self.extent = extent
        self.qtree = QuadTree(extent)
        self.init_dam(nparticles)

    def init_dam(self, nparticles):
        """
        Position particles in a verticle column.
        """
        qtree = self.qtree
        t, l, b, r = self.extent

        COLUMNS = 10
        PARTICLES_PER_COLUMN, remainder = divmod(nparticles, COLUMNS)

        width = r - l
        height = b - t
        dam_width = width / 5

        for column in np.linspace(l + dam_width, l + 2 * dam_width, COLUMNS):
            for row in np.linspace(t, b, PARTICLES_PER_COLUMN):
                qtree.insert(Particle((row, column)))

        for _ in range(remainder):
            qtree.insert(
                Particle(
                    (
                        np.random.random() * height + t,
                        np.random.random() * width + l,
                    )
                )
            )

    def step(self):
        """
        For each particle, compute densities and pressures, then forces, and
        finally integrate to obtain new positions.
        """
        self._density_pressure()
        self._forces()
        self._integrate()

    def _density_pressure(self):
        """
        for (auto &pi : particles)
        {
            pi.rho = 0.f;
            for (auto &pj : particles)
            {
                Vector2d rij = pj.x - pi.x;
                float r2 = rij.squaredNorm();

                if (r2 < HSQ)
                {
                    // this computation is symmetric
                    pi.rho += MASS * POLY6 * pow(HSQ - r2, 3.f);
                }
            }
            pi.p = GAS_CONST * (pi.rho - REST_DENS);
        }
        """

    def _forces(self):
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

    def _integrate(self):
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
