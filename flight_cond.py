from parapy.core import *
import numpy as np


class FlightCondition(Base):
    weight = Input(5000)  # kg.
    speed = Input(80)  # m/s.
    height = Input(1000)  # ft.
    units = Input('SI')

    @Attribute
    def atmos_calc(self):
        """ Import the atmospheric parameters table and interpolates if needed. """

        # Condition to check if the input height is valid.
        if self.height < -1e3 or self.height > 65e3:
            print('This flight level is not allowed!')
            return

        # Conversion constants from imperial to SI. Order constructed according to the flight_params vector below.
        conv_cnsts = [0.453592, 0.3048, 0.3048, np.NaN, 0.0208854, 47.8803, 515.378818, 0.3048,
                      14.5939 / 0.3048, 0.3048 ** 2]

        # Table values are in imperial units.
        atmos_matrix = np.genfromtxt('inputs/atmos_params.csv', delimiter=',', dtype=float, skip_header=True)
        atmos_matrix[:, 0] *= 1e3

        # Linearly interpolating the values.
        atmos_vector = []
        for i in range(len(atmos_matrix) - 1):
            if atmos_matrix[i, 0] <= self.height < atmos_matrix[i + 1, 0]:
                ratio = (self.height - atmos_matrix[i, 0]) / (atmos_matrix[i + 1, 0] - atmos_matrix[i, 0])
                for j in [0, 4, 5, 6, 7, 8, 9]:
                    interp_value = atmos_matrix[i, j] + (atmos_matrix[i + 1, j] - atmos_matrix[i, j]) * ratio
                    atmos_vector.append(interp_value)

        # Converting values according to units.
        if self.units == 'SI':
            for i in range(len(atmos_vector)):
                if i == 1:
                    atmos_vector[i] = (atmos_vector[i] - 491.67) * 5 / 9
                else:
                    atmos_vector[i] *= conv_cnsts[i + 2]
        else:
            self.weight /= conv_cnsts[0]
            self.speed /= conv_cnsts[1]

        flight_params = [self.weight, self.speed] + atmos_vector + [self.units]
        return flight_params
