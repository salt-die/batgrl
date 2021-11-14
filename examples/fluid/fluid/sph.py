import numpy as np

from nurses_2.data_structures import Size


class SPHSolver:
    def __init__(self, size: Size, nparticles=1000):
        self.nparticles = nparticles
        self.resize(size)

    def resize(self, size: Size):
        self.size = size

        nparticles = self.nparticles
        self.state = np.zeros((nparticles, 8), dtype=float)

        # Buffers
        self._relatives_buffer = np.zeros((nparticles, nparticles, 2))
        self._relatives_sqr_buffer = np.zeros_like(self._relatives_buffer)
        self._distance_sqr_buffer = np.zeros((nparticles, nparticles), dtype=float)
        self._neighbors_buffer = np.zeros_like(self._distance_sqr_buffer, dtype=bool)
        self._lower_tri = np.tril_indices_from(self._distance_sqr_buffer)
        self._1d_buffer = np.zeros(nparticles)
        self._2d_buffer = np.zeros((nparticles, 2))

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
        REST_DENS = 100.0
        VISC = 2000.0 / (np.pi * H**5.0)
        POLY6 = 2.0 / (np.pi * H**8.0)
        SPIKY_GRAD = -5.0 / (np.pi * H**5.0)
        GRAVITY = 10.0

        state = self.state
        positions = state[:, :2]
        velocities = state[:, 2:4]
        acceleration = state[:, 4:6]
        densities = state[:, 6]
        pressure = state[:, 7]

        # Brute force neighbors:
        relatives = np.subtract(positions[None], positions[:, None], out=self._relatives_buffer)
        relatives_sqr = np.power(relatives, 2, out=self._relatives_sqr_buffer)
        distance_sqr = relatives_sqr.sum(axis=-1, out=self._distance_sqr_buffer)

        neighbors = np.less(distance_sqr, H**2, out=self._neighbors_buffer)
        neighbors[self._lower_tri] = False

        ys, xs = pairs = np.nonzero(neighbors)
        distance_sqr = distance_sqr[pairs]

        _pairs_buffer = np.zeros_like(distance_sqr)
        _1d_buffer = self._1d_buffer

        # Density / Pressure update ####################################
        densities[:] = REST_DENS                                       #
                                                                       #
        np.subtract(H, distance_sqr, out=_pairs_buffer)                #
        np.power(_pairs_buffer, 3, out=_pairs_buffer)                  #
        density = np.multiply(_pairs_buffer, POLY6, out=_pairs_buffer) #
        densities[ys] += density                                       #
        densities[xs] += density                                       #
                                                                       #
        np.subtract(densities, REST_DENS, out=_1d_buffer)              #
        np.multiply(GAS_CONST, _1d_buffer, out=pressure)               #
        ################################################################

        # Forces update #######################################################
        acceleration[:] = 0.0                                                 #
                                                                              #
        y_dens = densities[ys][:, None]                                       #
        x_dens = densities[xs][:, None]                                       #
                                                                              #
        distances = np.sqrt(distance_sqr)[:, None]                            #
        normals = relatives[pairs] / distances                                #
        strengths = np.subtract(H, distances, out=distances)                  #
                                                                              #
        _skinny_buffer = (pressure[ys] + pressure[xs])[:, None]               #
        _fat_buffer = SPIKY_GRAD * normals                                    #
        np.multiply(_fat_buffer, _skinny_buffer, out=_fat_buffer)             #
        np.power(strengths, 3, out=_skinny_buffer)                            #
        forces_ij = np.multiply(_fat_buffer, _skinny_buffer, out=_fat_buffer) #
                                                                              #
        _fat_buffer_2 = forces_ij / x_dens                                    #
                                                                              #
        acceleration[ys] += _fat_buffer_2                                     #
        acceleration[xs] -= np.divide(forces_ij, y_dens, out=_fat_buffer_2)   #
                                                                              #
        np.subtract(velocities[xs], velocities[ys], out=_fat_buffer)          #
        np.multiply(VISC, _fat_buffer, out=_fat_buffer)                       #
        viscs_ij = np.multiply(strengths, _fat_buffer, out=_fat_buffer)       #
                                                                              #
        acceleration[ys] += np.divide(viscs_ij, x_dens, out=_fat_buffer_2)    #
        acceleration[xs] -= np.divide(viscs_ij, y_dens, out=_fat_buffer_2)    #
                                                                              #
        acceleration[:, 0] += np.divide(GRAVITY, densities, out=_1d_buffer)   #
        #######################################################################

        # Integrate
        velocities += np.divide(acceleration, densities[:, None], self._2d_buffer)
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
        velocities[top] *= -.5             #
        velocities[left] *= -.5            #
        velocities[bottom] *= -.5          #
        velocities[right] *= -.5           #
        ####################################
