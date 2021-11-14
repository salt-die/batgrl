import numpy as np
from numpy import pi
from scipy.spatial import KDTree

from nurses_2.data_structures import Size


class SPHSolver:
    def __init__(self, size: Size, nparticles=1000):
        self.nparticles = nparticles
        self.resize(size)

    def resize(self, size: Size):
        self.size = size
        self.state = np.zeros((self.nparticles, 8), dtype=float)
        self.init_dam()

    def init_dam(self):
        """
        Position particles in a verticle column.
        """
        height, width = self.size
        dam_width = width / 5

        positions = self.state[:, :2]

        positions[:] = np.random.random((self.nparticles, 2))
        positions[:] *= height, dam_width
        positions[:, 1] += dam_width

    def step(self):
        """
        For each particle, compute densities and pressures, then forces, and
        finally integrate to obtain new positions.
        """
        H = 1.44
        GAS_CONST = 2000.0
        REST_DENS = 25.0
        VISC = 100.0
        POLY6 = 2.0 / (np.pi * H**8.0)
        SPIKY_GRAD = -10.0 / (np.pi * H**5.0)
        VISC_LAP = 20.0 / (np.pi * H**5.0)
        GRAVITY = 10.0

        state = self.state
        positions = state[:, :2]
        velocities = state[:, 2:4]
        acceleration = state[:, 4:6]
        densities = state[:, 6]
        pressure = state[:, 7]

        norm = np.linalg.norm

        pairs = KDTree(positions).query_pairs(H)

        # Density / Pressure update ######################################
        densities[:] = REST_DENS                                         #
                                                                         #
        for i, j in pairs:                                               #
            density = POLY6 * (H - norm(positions[i] - positions[j]))**3 #
            densities[i] += density                                      #
            densities[j] += density                                      #
                                                                         #
        pressure[:] = GAS_CONST * (densities - REST_DENS)                #
        ##################################################################

        # Forces update ######################################################################
        acceleration[:] = 0.0                                                                #
                                                                                             #
        for i, j in pairs:                                                                   #
            relative = positions[i] - positions[j]                                           #
            distance = norm(relative)                                                        #
                                                                                             #
            normal = relative / distance                                                     #
                                                                                             #
            strength = H - distance                                                          #
                                                                                             #
            force_ij = -normal * (pressure[i] + pressure[j]) * SPIKY_GRAD * strength**3 * .5 #
            visc_ij = VISC * (velocities[j] - velocities[i]) * VISC_LAP * strength           #
                                                                                             #
            acceleration[i] += force_ij / densities[j]                                       #
            acceleration[i] += visc_ij / densities[j]                                        #
                                                                                             #
            acceleration[j] += -force_ij / densities[i]                                      #
            acceleration[j] += -visc_ij / densities[i]                                       #
                                                                                             #
        acceleration[:, 0] += GRAVITY / densities                                            #
        ######################################################################################

        # Integrate
        velocities += acceleration / densities[:, None]
        positions += velocities

        # Move out-of-bounds particles #####
        h, w = self.size                   #
        ys, xs = positions.T               #
                                           #
        top = ys < 0                       #
        left = xs < 0                      #
        bottom = ys >= h                   #
        right = xs >= w                    #
                                           #
        ys[top]     = -ys[top]             #
        xs[left]    = -xs[left]            #
        ys[bottom] -= 2 * (ys[bottom] - h) #
        xs[right]  -= 2 * (xs[right] - w)  #
                                           #
        velocities[:, 0][top] *= -.5       #
        velocities[:, 1][left] *= -.5      #
        velocities[:, 0][bottom] *= -.5    #
        velocities[:, 1][right] *= -.5     #
        ####################################
