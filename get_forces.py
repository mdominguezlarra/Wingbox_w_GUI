from parapy.core import *
import numpy as np


class GetForces(Base):
    input_case = Input()  # Load case to be considered.
    flight_cond = Input()  # Flight condition parameters.
    num_case = Input(0)

    # Treating AVL output data to get parameters and coefficients for wing semispan.
    @Input
    def data_treatment(self):
        raw_data = self.input_case.results[self.num_case]['StripForces']['Wing']
        idx = len(raw_data['Chord']) // 2
        if int(len(raw_data['Chord']) % 2) == 1:
            idx = + 1

        # Retrieving parameters and coefficients.
        y_pos = raw_data['Yle'][0:idx]
        chords = raw_data['Chord'][0:idx]
        areas = raw_data['Area'][0:idx]
        cl_lst = raw_data['cl'][0:idx]
        cd_lst = raw_data['cd'][0:idx]
        cm_c4_lst = raw_data['cm_c/4'][0:idx]

        # Retrieving flight condition parameters.
        V = self.flight_cond.atmos_calc[1]
        rho = self.flight_cond.atmos_calc[5]

        return y_pos, chords, areas, cl_lst, cd_lst, cm_c4_lst, V, rho

    @Attribute
    def forces_moms_pos(self):

        spar_interp_pts = []
        x_poly_coeffs = []
        z_poly_coeffs = []
        y_pos = self.data_treatment[0]
        spar_curves = self.input_case.wing.wingbox.spars.front_spar_intersec_curves
        spans = self.input_case.wing.spans

        # Defining control points to be used in the interpolation.
        ctrl_pts = []
        for spar_curve in spar_curves:
            control_pt = spar_curve.control_points[0]
            if float(round(control_pt[1])) in spans:
                ctrl_pts.append(control_pt)

        for k in range(len(ctrl_pts) - 1):
            first_pt = ctrl_pts[k]
            second_pt = ctrl_pts[k + 1]

            # Getting the points to fit the polynomial.
            x_pts = np.array([first_pt[0], second_pt[0]])
            y_pts = np.array([first_pt[1], second_pt[1]])
            z_pts = np.array([first_pt[2], second_pt[2]])

            x_poly_coeffs.append(np.polyfit(y_pts, x_pts, 1).tolist())
            z_poly_coeffs.append(np.polyfit(y_pts, z_pts, 1).tolist())

        # Finding AVL force locations along the spar by interpolation.
        interp_idx = 0
        for y in y_pos:
            if y > spans[interp_idx + 1]:
                interp_idx += 1

            x_interp = x_poly_coeffs[interp_idx][0] * y + x_poly_coeffs[interp_idx][1]
            z_interp = z_poly_coeffs[interp_idx][0] * y + z_poly_coeffs[interp_idx][1]

            spar_interp_pts.append((float(x_interp), y, float(z_interp)))

        return spar_interp_pts

    # Getting forces and moments.
    @Attribute
    def forces_moms(self):
        y_pos, chords, areas, cl_lst, cd_lst, cm_c4_lst, V, rho = self.data_treatment

        L_vector = []
        D_vector = []
        M_vector = []

        for k in range(len(cl_lst)):
            L_vector.append(0.5 * rho * (V ** 2) * areas[k] * cl_lst[k])
            D_vector.append(0.5 * rho * (V ** 2) * areas[k] * cd_lst[k])
            M_vector.append(0.5 * rho * (V ** 2) * areas[k] * chords[k] * cm_c4_lst[k])

        return L_vector, D_vector, M_vector
