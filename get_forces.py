from parapy.core import *
import numpy as np


class GetForces(Base):
    input_case = Input()  # Load case to be considered.
    flight_cond = Input()  # Flight condition parameters.
    num_case = Input(0)

    @Input
    def data_treatment(self):
        raw_data = self.input_case.results[self.num_case]['StripForces']['Wing']
        idx = len(raw_data['Chord']) // 2
        if int(len(raw_data['Chord']) % 2) == 1:
            idx = + 1

        # Retrieving important values.
        y_pos = raw_data['Yle'][0:idx]
        chords = raw_data['Chord'][0:idx]
        areas = raw_data['Area'][0:idx]
        cl_lst = raw_data['cl'][0:idx]
        cd_lst = raw_data['cd'][0:idx]
        cm_c4_lst = raw_data['cm_c/4'][0:idx]

        V = self.flight_cond.atmos_calc[1]
        rho = self.flight_cond.atmos_calc[5]

        return y_pos, chords, areas, cl_lst, cd_lst, cm_c4_lst, V, rho

    @Attribute
    def forces_and_moments(self):
        y_pos, chords, areas, cl_lst, cd_lst, cm_c4_lst, V, rho = self.data_treatment

        L_vector = []
        D_vector = []
        M_vector = []

        for k in range(len(cl_lst)):
            L_vector.append(0.5 * rho * (V ** 2) * areas[k] * cl_lst[k])
            D_vector.append(0.5 * rho * (V ** 2) * areas[k] * cd_lst[k])
            M_vector.append(0.5 * rho * (V ** 2) * areas[k] * chords[k] * cm_c4_lst[k])

        print(L_vector)
        print(D_vector)
        print(M_vector)

        return L_vector, D_vector, M_vector
