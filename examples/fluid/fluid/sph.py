import numpy as np
from scipy.spatial import KDTree

from nurses_2.data_structures import Size

H = .8
GAS_CONST = 3000.0
REST_DENS = 300.0
POLY6 = 1.0 / (np.pi * H**8.0)
VISC = 4000.0 / (np.pi * H**5.0)
SPIKY_GRAD = -5.0 / (np.pi * H**5.0)
GRAVITY = 40.0


class SPHSolver:
    def __init__(self, size: Size, nparticles=1000):
        self.nparticles = nparticles
        self.resize(size)

    def resize(self, size: Size):
        self.size = size

        nparticles = self.nparticles
        self.state = np.zeros((nparticles, 8), dtype=float)

        self.init_dam()

    def init_dam(self):
        """
        Position particles in a verticle column.
        """
        height, width = self.size
        dam_width = width / 5

        positions = self.state[:, :2]

        positions[:] = np.random.random((self.nparticles, 2))
        positions *= height, dam_width
        positions[:, 1] += (width - dam_width) / 2

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

        ys, xs = KDTree(positions).query_pairs(H, output_type='ndarray').T

        relatives = positions[xs] - positions[ys]
        distances = np.linalg.norm(relatives, axis=-1)

        strengths = H - distances
        str_cubed = strengths ** 3

        # Density / Pressure update #######################
        density = POLY6 * str_cubed                       #
                                                          #
        densities[:] = REST_DENS                          #
        densities[ys] += density                          #
        densities[xs] += density                          #
                                                          #
        pressure[:] = GAS_CONST * (densities - REST_DENS) #
        ###################################################

        # Forces update ##############################
        pressure_yx = (                              #
            SPIKY_GRAD                               #
            * relatives                              #
            / distances[:, None]                     #
            * (pressure[xs] + pressure[ys])[:, None] #
            * str_cubed[:, None]                     #
        )                                            #
                                                     #
        viscs_yx = (                                 #
            VISC                                     #
            * (velocities[xs] - velocities[ys])      #
            * strengths[:, None]                     #
         )                                           #
                                                     #
        total = pressure_yx + viscs_yx               #
                                                     #
        acceleration[:, 0] += GRAVITY / densities    #
                                                     #
        densities = densities[:, None]               #
        acceleration[ys] += total / densities[xs]    #
        acceleration[xs] -= total / densities[ys]    #
                                                     #
        ##############################################

        # Integrate
        velocities += acceleration / densities
        positions += velocities

        # Move out-of-bounds particles ##
        h, w = self.size                #
        ys, xs = positions.T            #
        vys, vxs = velocities.T         #
                                        #
        top = ys < 0                    #
        left = xs < 0                   #
        bottom = ys >= h                #
        right = xs >= w                 #
                                        #
        ys[top]    *= -1                #
        xs[left]   *= -1                #
        ys[bottom] = 2 * h - ys[bottom] #
        xs[right]  = 2 * w - xs[right]  #
                                        #
        vys[top]    *= -.5              #
        vxs[left]   *= -.5              #
        vys[bottom] *= -.5              #
        vxs[right]  *= -.5              #
        #################################

        acceleration[:] = 0.0  # Reset forces
