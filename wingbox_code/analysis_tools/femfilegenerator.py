from parapy.core import *
from parapy.geom import *
from parapy.lib.nastran.entry import *
from parapy.lib.nastran.writer import *
from parapy.mesh import EdgeGroup
from parapy.mesh.salome import Mesh, Tri
from parapy.cae.nastran import read_pch
from .get_forces import GetForces
from .generalfuse import GeneralFuse
import numpy as np
import csv
import os


# Function to find the mechanical properties of a material given a characteristic string.
def mat_props_finder(mat_str: str):
    cvs_units = [6.894757e6, 6.894757e6, 6.894757e6, 1, 515.378818, 6.894757e6, 6.894757e6, 6.894757e6]

    # Finding characteristic parameters of input material.
    split_mat_str = mat_str.split('-')
    t = float(split_mat_str[2]) / 25.4  # Conversion to imperial units
    split_mat_str.pop(2)
    id = '-'.join(split_mat_str)

    # Finding the correct mechanical properties.
    path = 'wingbox_code/input_data/materials.csv'
    with open(path, 'r', newline='') as file:
        mat_file = csv.reader(file)
        for idx, row in enumerate(mat_file):
            if idx == 0:
                header = row[6:len(row) - 1]
                header.append('t')
            else:
                row_str = row[1] + '-' + row[2] + '-' + row[5]
                t_m, t_p = float(row[3]), float(row[4])
                if id == row_str and t_m < t < t_p:
                    prop_lst = [float(row[k]) * cvs_units[k - 6] for k in range(6, len(row) - 1)]
                    prop_lst.append(t)
                    prop_dict = {key: value for (key, value) in zip(header, prop_lst)}

                    return prop_dict


# Function to find cross-section properties for 1D elements.
def sec_props_finder(arg):
    props_lst = []
    for lst in arg:
        values, typ = lst
        if typ == 'dims':
            l, a = values[0] * 1e-3, (values[0] / 2) * 1e-3  # conversion to m.
            h, b = values[1] * 1e-3, (values[1] / 2) * 1e-3  # conversion to m.

            # Properties calculation.
            A = l * h  # Area.
            I1 = l ** 3 * (h / 12)  # Moment of inertia aligned with y direction.
            I2 = h ** 3 * (l / 12)  # Moment of inertia aligned with z direction.
            J = a * b ** 3 * ((16 / 3) - 3.36 * (b / a) * (1 - (b ** 4 / (12 * a ** 4))))  # Polar moment of inertia.

            props_lst.append([A, I1, I2, J])

        elif typ == 'moms':
            props_lst.append(values)

    return props_lst


def pt_finder(obj, pt, tol):
    while not obj.mesh.grid.find_node_at(pt, tolerance=tol):
        tol *= 10
    return obj.mesh.grid.find_node_at(pt, tolerance=tol)


class FEMFileGenerator(GeomBase):
    wing = Input()
    analysis = Input()
    mat_2D = Input([
        'Al2024-T3-1.27-A',  # SKIN
        'Al2024-T3-1.27-A',  # SPAR WEB
        'Al2024-T3-1.27-A'])  # RIBS
    mat_1D = Input([
        'Al7475-T61-1.524-S',  # STRINGERS
        'Al7475-T61-1.524-S',  # SPAR CAPS
        'Al7475-T61-1.524-S'])  # RIB CAPS
    tc_select = Input('t')  # TENSION OR COMPRESSION SELECTOR
    secs = Input([[[1, 1], 'dims'],  # STRINGERS
                  [[1, 1], 'dims'],  # SPAR CAPS
                  [[1, 0.0833, 0.0833, 2.2533], 'moms']])  # RIB CAPS
    bcs = Input(['root_rib', '123456'])

    # CONTROLS
    quad_dominance = Input(False)  # or True
    min_elem_size = Input(0.01)
    max_elem_size = Input(0.1)

    # Same material is used throughout all elements of a component.
    @Input
    def mat_props(self):
        mat_lst = []
        mat_in = self.mat_2D + self.mat_1D
        for mat in mat_in:
            mat_lst.append(mat_props_finder(mat))

        return mat_lst  # 2D props and 1D props lists.

    @Part
    def cases(self):
        """
        Retrieves and calculates the forces from AVL
        :return: GetForces
        """
        return GetForces(quantify=len(self.analysis.case_settings[2]),
                         input_case=self.analysis,
                         num_case=child.index + 1,
                         flight_cond=self.analysis.flight_cond)

    # Creation of parts for FEM mesh.
    @Part
    def general_shape(self):
        return GeneralFuse(tools=self.wing.STEP_node_list,
                           fuzzy_value=1e-3)

    @Part
    def mesh_seed(self):
        return Tri(shape_to_mesh=self.general_shape,
                   min_size=self.min_elem_size,
                   max_size=self.max_elem_size,
                   only_2d=False,
                   quad_dominant=self.quad_dominance)

    @Part
    def mesh(self):
        return Mesh(shape_to_mesh=self.general_shape,
                    controls=[self.mesh_seed])

    # NASTRAN file writing.
    @Attribute
    def FEMentries(self):
        entries = []

        # Defining materials to be used.
        mat_2d = [[MAT1(E=mat['E' + self.tc_select], NU=mat['nu'], RHO=mat['rho']), mat['t']] for idx, mat in
                  enumerate(self.mat_props) if idx <= 2]
        mat_1d = [MAT1(E=mat['E' + self.tc_select], NU=mat['nu']) for idx, mat in enumerate(self.mat_props) if idx > 2]


        # Defining element properties.
        props_1d = [PBAR(MID=mat, A=props[0], I1=props[1], I2=props[2], J=props[3]) for
                    mat, props in zip(mat_1d, sec_props_finder(self.secs))]
        props_2d = [PSHELL(MID1=mat[0], T=mat[1], MID2=mat[0], MID3=mat[0]) for mat in mat_2d]


        # Creating grid for the FEM model.
        mesh_id_to_GRID = {}
        for node in self.mesh.grid.nodes:
            grid = GRID(ID=node.mesh_id, X1=node.x, X2=node.y, X3=node.z)
            mesh_id_to_GRID[node.mesh_id] = grid
            entries.append(grid)


        # Appending the finite elements to be used in the model.
        elms = []
        for idx, face in enumerate(self.mesh.grid.faces):
            nodes = [mesh_id_to_GRID[node.mesh_id] for node in face.nodes]
            if len(nodes) == 3:
                elm = CTRIA3(PID=props_2d[0], G1=nodes[0], G2=nodes[1], G3=nodes[2])
                elms.append(elm)
            elif len(nodes) == 4:
                elm = CQUAD4(PID=props_2d[0], G1=nodes[0], G2=nodes[1], G3=nodes[2], G4=nodes[3])
                elms.append(elm)
        entries.extend(elms)


        # BCs placement for front and rear spars and root rib.
        bc_lst, bc_const = [], []
        # If constraining root rib.
        for bc in self.bcs:
            if bc[0] == 'root_rib':
                tol = 1e-7
                # Getting all the points in the root rib.
                obj = self.general_shape.vertices
                pts = [obj[k].point for k in range(len(obj)) if obj[k].point[1] < 1e-6]

                # Popping last skin vertices values.
                x_coords = [pt[0] for pt in pts]
                pts.pop(x_coords.index(max(x_coords)))
                x_coords.pop(x_coords.index(max(x_coords)))
                pts.pop(x_coords.index(max(x_coords)))

                bc_lst_aux = [pt_finder(self, pt, tol).mesh_id for pt in pts]
                bc_const_aux = [bc[1]] * len(bc_lst_aux)
                bc_lst.extend(bc_lst_aux)
                bc_const.extend(bc_const_aux)

            elif bc[0] == 'front_spar':
                tol = 1e-7
                bc_lst_aux = [
                    pt_finder(self, self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[0], tol).mesh_id,
                    pt_finder(self, self.wing.spars.spars[0].cutter_intersec_curves[0].control_points[1], tol).mesh_id]
                bc_const_aux = [bc[1]] * len(bc_lst_aux)
                bc_lst.extend(bc_lst_aux)
                bc_const.extend(bc_const_aux)

            elif bc[0] == 'rear_spar':
                tol = 1e-7
                bc_lst_aux = [
                    pt_finder(self, self.wing.spars.spars[1].cutter_intersec_curves[0].control_points[0], tol).mesh_id,
                    pt_finder(self, self.wing.spars.spars[1].cutter_intersec_curves[0].control_points[1], tol).mesh_id]
                bc_const_aux = [bc[1]] * len(bc_lst_aux)
                bc_lst.extend(bc_lst_aux)
                bc_const.extend(bc_const_aux)

        for SID in range(len(self.cases)):
            spc1 = [SPC1(SID=SID+1, C=bc_const[idx], Gi=bc_lst[idx]) for idx, _ in enumerate(bc_lst)]
            entries.extend(spc1)


        # Defining forces and their locations for each case.
        forces = []
        load_cases = self.cases
        for idx_SID, load_case in enumerate(load_cases):
            idx_load = 0
            p_lst = []
            forces_moms = load_case.forces_moms
            pos = load_case.forces_moms_pos

            for point in pos:
                tol = 1e-7
                pt = pt_finder(self, point, tol)
                force_id = pt.mesh_id

                # Calculate force and append it to list.
                L_load = FORCE(SID=idx_SID+1, G=force_id, F=forces_moms[idx_load][0], N1=0, N2=0, N3=1)
                D_load = FORCE(SID=idx_SID+1, G=force_id, F=forces_moms[idx_load][1], N1=1, N2=0, N3=0)
                M_load = Moment(SID=idx_SID+1, G=force_id, M=forces_moms[idx_load][2], N1=0, N2=1, N3=0)
                load_lst = [L_load, D_load, M_load]
                p_lst.extend(load_lst)

                idx_load += 1

            forces.extend(p_lst)

        entries.extend(forces)

        return entries

    @Attribute
    def FEMWriter(self):
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, '..', 'bdf_files', 'bdf_templates', 'wingbox_template.bdf')
        return Writer(self.FEMentries,
                      template_path=template_path,
                      template_values={'SID': [idx + 1 for idx, _ in enumerate(self.cases)]})
